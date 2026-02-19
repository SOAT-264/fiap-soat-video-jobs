import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from job_service.infrastructure.adapters.output.video_processing.ffmpeg_processor import FFmpegVideoProcessor


@pytest.mark.asyncio
async def test_get_video_duration_success(monkeypatch):
    processor = FFmpegVideoProcessor()

    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: Mock(returncode=0, stdout="12.5\n", stderr=""),
    )

    duration = await processor._get_video_duration("video.mp4")
    assert duration == 12.5


@pytest.mark.asyncio
async def test_extract_frames_success(tmp_path, monkeypatch):
    processor = FFmpegVideoProcessor()
    output_dir = tmp_path / "frames"

    async def fake_duration(_):
        return 2.0

    monkeypatch.setattr(processor, "_get_video_duration", fake_duration)

    def fake_run(*args, **kwargs):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "frame_0001.jpg").write_bytes(b"1")
        (output_dir / "frame_0002.jpg").write_bytes(b"2")
        return Mock(returncode=0, stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    progress = []
    count = await processor.extract_frames("in.mp4", str(output_dir), progress_callback=progress.append)

    assert count == 2
    assert progress[-1] == 100


@pytest.mark.asyncio
async def test_extract_frames_raises_on_ffmpeg_error(monkeypatch, tmp_path):
    processor = FFmpegVideoProcessor()

    async def fake_duration(_):
        return 1.0

    monkeypatch.setattr(processor, "_get_video_duration", fake_duration)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: Mock(returncode=1, stderr="ffmpeg error"),
    )

    with pytest.raises(RuntimeError):
        await processor.extract_frames("in.mp4", str(tmp_path / "out"))


@pytest.mark.asyncio
async def test_create_zip_archive_reports_progress(tmp_path):
    processor = FFmpegVideoProcessor()
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    for i in range(3):
        (frames_dir / f"frame_{i:04d}.jpg").write_bytes(b"x")

    zip_file = tmp_path / "frames.zip"
    progress = []

    size = await processor.create_zip_archive(str(frames_dir), str(zip_file), progress_callback=progress.append)

    assert size == os.path.getsize(zip_file)
    assert progress[-1] == 100
    assert Path(zip_file).exists()
