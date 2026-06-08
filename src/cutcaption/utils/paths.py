"""Path discovery and output naming helpers."""

from __future__ import annotations

from pathlib import Path

from cutcaption.models import VIDEO_EXTENSIONS, VideoJob


def discover_videos(input_path: Path) -> list[Path]:
    path = input_path.expanduser()
    if path.is_file():
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            raise ValueError(f"Unsupported video extension: {path.suffix or '(none)'}")
        return [path]

    if path.is_dir():
        videos = sorted(
            item
            for item in path.iterdir()
            if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS
        )
        if not videos:
            raise FileNotFoundError(f"No supported video files found in: {path}")
        return videos

    raise FileNotFoundError(f"Input does not exist: {path}")


def default_output_dir(input_path: Path, videos: list[Path]) -> Path:
    path = input_path.expanduser()
    if path.is_dir() or len(videos) > 1:
        return path / "captioned"
    return videos[0].parent


def build_video_job(video_path: Path, output_dir: Path) -> VideoJob:
    stem = video_path.stem
    return VideoJob(
        source=video_path,
        srt_path=output_dir / f"{stem}.srt",
        ass_path=output_dir / f"{stem}.ass",
        rendered_path=output_dir / f"{stem}_captioned.mp4",
    )
