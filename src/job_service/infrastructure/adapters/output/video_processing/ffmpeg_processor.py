"""FFmpeg Video Processing adapter."""
import os
import subprocess
import tempfile
import zipfile
from typing import Callable, Optional
from pathlib import Path


class FFmpegVideoProcessor:
    """Video processor using FFmpeg for frame extraction."""

    def __init__(self, temp_dir: Optional[str] = None):
        self._temp_dir = temp_dir or tempfile.gettempdir()

    async def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        fps: float = 1.0,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> int:
        """
        Extract frames from video at specified FPS rate.
        
        Args:
            video_path: Path to input video
            output_dir: Directory for extracted frames
            fps: Frames per second to extract
            progress_callback: Optional callback for progress updates
            
        Returns:
            Number of frames extracted
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Get video duration first
        duration = await self._get_video_duration(video_path)
        total_frames = int(duration * fps) if duration else 0
        
        # Extract frames using FFmpeg
        output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={fps}",
            "-q:v", "2",
            output_pattern,
            "-y",
        ]
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        
        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {process.stderr}")
        
        # Count extracted frames
        frame_files = list(Path(output_dir).glob("frame_*.jpg"))
        frame_count = len(frame_files)
        
        if progress_callback:
            progress_callback(100)
        
        return frame_count

    async def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
        return 0.0

    async def create_zip_archive(
        self,
        source_dir: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> int:
        """
        Create a ZIP archive from extracted frames.
        
        Args:
            source_dir: Directory containing frames
            output_path: Path for output ZIP file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Size of created ZIP file in bytes
        """
        frame_files = sorted(Path(source_dir).glob("frame_*.jpg"))
        total_files = len(frame_files)
        
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, frame_file in enumerate(frame_files):
                zf.write(frame_file, arcname=frame_file.name)
                
                if progress_callback and total_files > 0:
                    progress = int((idx + 1) / total_files * 100)
                    progress_callback(progress)
        
        return os.path.getsize(output_path)
