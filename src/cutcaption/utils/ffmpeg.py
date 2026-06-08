"""Subprocess helpers for ffmpeg and ffprobe."""

from __future__ import annotations

import shutil
import subprocess


def executable_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)
