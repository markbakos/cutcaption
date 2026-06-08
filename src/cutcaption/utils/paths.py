"""Path discovery and output naming helpers."""

from __future__ import annotations

from pathlib import Path

from cutcaption.models import VIDEO_EXTENSIONS, OutputPaths, VideoJob


def is_video_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS


def discover_inputs(input_path: Path, recursive: bool = False) -> list[Path]:
    path = input_path.expanduser()
    if path.is_file():
        if not is_video_file(path):
            supported = ", ".join(sorted(VIDEO_EXTENSIONS))
            raise ValueError(
                f"Unsupported file type: {path.name}. "
                f"Supported video extensions are: {supported}."
            )
        return [path]

    if path.is_dir():
        candidates = path.rglob("*") if recursive else path.iterdir()
        videos = sorted(
            item
            for item in candidates
            if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS
        )
        if not videos:
            supported = ", ".join(sorted(VIDEO_EXTENSIONS))
            raise FileNotFoundError(
                f"No supported video files found in {path}. "
                f"Supported extensions are: {supported}."
            )
        return videos

    raise FileNotFoundError(f"Input does not exist: {path}")


def build_output_paths(input_video: Path, output_dir: Path | None) -> OutputPaths:
    destination = output_dir.expanduser() if output_dir is not None else input_video.parent
    destination.mkdir(parents=True, exist_ok=True)
    stem = input_video.stem
    return OutputPaths(
        srt_path=destination / f"{stem}.srt",
        ass_path=destination / f"{stem}.ass",
        json_path=destination / f"{stem}.json",
        captioned_video_path=destination / f"{stem}_captioned.mp4",
    )


def folder_output_dir(input_path: Path, output_dir: Path | None) -> Path | None:
    if output_dir is not None:
        return output_dir
    path = input_path.expanduser()
    if path.is_dir():
        return path / "captioned"
    return None


def discover_videos(input_path: Path) -> list[Path]:
    return discover_inputs(input_path)


def default_output_dir(input_path: Path, videos: list[Path]) -> Path:
    if input_path.expanduser().is_dir() or len(videos) > 1:
        return input_path.expanduser() / "captioned"
    return videos[0].parent


def build_video_job(video_path: Path, output_dir: Path | None) -> VideoJob:
    output_paths = build_output_paths(video_path, output_dir)
    return VideoJob(
        source=video_path,
        srt_path=output_paths.srt_path,
        ass_path=output_paths.ass_path,
        json_path=output_paths.json_path,
        rendered_path=output_paths.captioned_video_path,
    )
