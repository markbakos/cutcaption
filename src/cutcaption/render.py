"""Video rendering boundary."""

from __future__ import annotations

from pathlib import Path

from cutcaption.utils.ffmpeg import FfmpegError, FfmpegNotFoundError, check_ffmpeg, run_command


class RenderError(FfmpegError):
    """Base error for video rendering failures."""


class OutputExistsError(RenderError):
    """Raised when a render target already exists and overwrite is disabled."""


def burn_subtitles(
    video_path: Path,
    ass_path: Path,
    output_path: Path,
    overwrite: bool = False,
) -> None:
    """Burn ASS subtitles into a video while preserving the original audio."""

    if not check_ffmpeg():
        raise FfmpegNotFoundError("ffmpeg not found. Install ffmpeg to burn subtitles into video.")
    if output_path.exists() and not overwrite:
        raise OutputExistsError(
            f"Output already exists: {output_path}. Pass overwrite=True to replace it."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_command(_burn_subtitles_command(video_path, ass_path, output_path, overwrite=overwrite))


def _burn_subtitles_command(
    video_path: Path,
    ass_path: Path,
    output_path: Path,
    *,
    overwrite: bool,
) -> list[str]:
    return [
        "ffmpeg",
        "-y" if overwrite else "-n",
        "-i",
        str(video_path),
        "-vf",
        f"subtitles=filename='{_escape_subtitle_filter_path(ass_path)}'",
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-c:a",
        "copy",
        str(output_path),
    ]


def _escape_subtitle_filter_path(path: Path) -> str:
    text = str(path)
    return (
        text.replace("\\", "\\\\")
        .replace("'", r"\'")
        .replace(":", r"\:")
        .replace(",", r"\,")
        .replace("[", r"\[")
        .replace("]", r"\]")
    )
