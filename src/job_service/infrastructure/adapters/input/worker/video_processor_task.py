"""Worker task for video processing."""
import os
import tempfile
import shutil
from uuid import UUID

from job_service.domain.entities.job import Job
from job_service.infrastructure.adapters.output.persistence import get_session_context
from job_service.infrastructure.adapters.output.persistence.repositories import SQLAlchemyJobRepository
from job_service.infrastructure.adapters.output.storage import S3StorageAdapter
from job_service.infrastructure.adapters.output.video_processing import FFmpegVideoProcessor
from job_service.infrastructure.adapters.output.messaging import EventPublisher
from job_service.infrastructure.adapters.output.cache import get_redis
from job_service.infrastructure.config import get_settings
from video_processor_shared.domain.exceptions import InvalidJobTransitionError
from video_processor_shared.domain.value_objects import JobStatus

settings = get_settings()


async def process_video_task(job_id: str, video_key: str) -> None:
    """
    Process a video job: download video, extract frames, create ZIP, upload.
    
    Args:
        job_id: Job UUID
        video_key: S3 key for the input video
    """
    storage = S3StorageAdapter()
    processor = FFmpegVideoProcessor()
    redis = await get_redis()
    publisher = EventPublisher(redis)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        async with get_session_context() as session:
            repository = SQLAlchemyJobRepository(session)
            
            # Get job
            job = await repository.find_by_id(UUID(job_id))
            if not job:
                raise ValueError(f"Job {job_id} not found")

            if job.is_terminal:
                return

            if job.status == JobStatus.PROCESSING:
                return
            
            # Start processing
            try:
                job.start()
            except InvalidJobTransitionError:
                return

            await repository.update(job)
            await session.commit()
            
            await publisher.publish_job_started(
                job_id=str(job.id),
                video_id=str(job.video_id),
                user_id=str(job.user_id),
            )
            
            # Download video
            video_path = os.path.join(temp_dir, "input_video")
            await storage.download_file(
                bucket=settings.S3_INPUT_BUCKET,
                key=video_key,
                destination=video_path,
            )
            
            job.update_progress(10)
            await repository.update(job)
            await session.commit()
            
            # Extract frames
            frames_dir = os.path.join(temp_dir, "frames")
            
            def update_extraction_progress(progress: int):
                # Map 0-100 to 10-70
                mapped = 10 + int(progress * 0.6)
                job.update_progress(min(mapped, 70))
            
            frame_count = await processor.extract_frames(
                video_path=video_path,
                output_dir=frames_dir,
                fps=1.0,
                progress_callback=update_extraction_progress,
            )
            
            job.update_progress(70)
            await repository.update(job)
            await session.commit()
            
            # Create ZIP archive
            zip_path = os.path.join(temp_dir, f"frames_{job_id}.zip")
            
            def update_zip_progress(progress: int):
                # Map 0-100 to 70-90
                mapped = 70 + int(progress * 0.2)
                job.update_progress(min(mapped, 90))
            
            zip_size = await processor.create_zip_archive(
                source_dir=frames_dir,
                output_path=zip_path,
                progress_callback=update_zip_progress,
            )
            
            job.update_progress(90)
            await repository.update(job)
            await session.commit()
            
            # Upload ZIP to S3
            output_key = f"outputs/{job.user_id}/{job_id}/frames.zip"
            await storage.upload_file(
                file_path=zip_path,
                bucket=settings.S3_OUTPUT_BUCKET,
                key=output_key,
                content_type="application/zip",
            )
            
            # Complete job
            job.complete(
                frame_count=frame_count,
                zip_path=output_key,
                zip_size=zip_size,
            )
            await repository.update(job)
            await session.commit()
            
            await publisher.publish_job_completed(
                job_id=str(job.id),
                video_id=str(job.video_id),
                user_id=str(job.user_id),
                frame_count=frame_count,
                zip_path=output_key,
            )
            
    except Exception as e:
        # Handle failure
        async with get_session_context() as session:
            repository = SQLAlchemyJobRepository(session)
            job = await repository.find_by_id(UUID(job_id))
            if job and not job.is_terminal:
                job.fail(str(e))
                await repository.update(job)
                await session.commit()
                
                await publisher.publish_job_failed(
                    job_id=str(job.id),
                    video_id=str(job.video_id),
                    user_id=str(job.user_id),
                    error_message=str(e),
                )
        raise
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
