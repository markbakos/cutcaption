"""Media probing boundary."""

from __future__ import annotations

from pathlib import Path

from cutcaption.utils.ffmpeg import run_command


def probe_duration(path: Path) -> float:
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(result.stdout.strip())
