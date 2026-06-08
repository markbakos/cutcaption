"""Video rendering boundary."""

from __future__ import annotations

from pathlib import Path

from cutcaption.utils.ffmpeg import run_command


def burn_subtitles(video_path: Path, ass_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"subtitles={ass_path}",
            "-c:a",
            "copy",
            str(output_path),
        ]
    )
    return output_path
