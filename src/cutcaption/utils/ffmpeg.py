"""Subprocess helpers for ffmpeg and ffprobe."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class FfmpegError(RuntimeError):
    """Base error for ffmpeg integration failures."""


class FfmpegNotFoundError(FfmpegError):
    """Raised when ffmpeg or ffprobe cannot be found."""


class FfmpegCommandError(FfmpegError):
    """Raised when an ffmpeg command exits unsuccessfully."""


class MediaProbeError(FfmpegError):
    """Raised when ffprobe output cannot be read."""


@dataclass(frozen=True, slots=True)
class MediaInfo:
    path: Path
    duration: float | None
    width: int | None
    height: int | None
    video_codec: str | None
    audio_codec: str | None
    has_audio: bool


def executable_exists(name: str) -> bool:
    return shutil.which(name) is not None


def check_ffmpeg() -> bool:
    return executable_exists("ffmpeg")


def check_ffprobe() -> bool:
    return executable_exists("ffprobe")


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise FfmpegNotFoundError(f"Required executable not found: {command[0]}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or "No stderr output."
        raise FfmpegCommandError(
            f"{command[0]} failed with exit code {result.returncode}: {stderr}"
        )
    return result


def probe_media(path: Path) -> MediaInfo:
    if not check_ffprobe():
        raise FfmpegNotFoundError("ffprobe not found. Install ffmpeg to inspect media files.")

    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise MediaProbeError(f"Could not parse ffprobe output for {path}.") from exc

    streams = payload.get("streams", [])
    if not isinstance(streams, list):
        raise MediaProbeError(f"Unexpected ffprobe stream output for {path}.")

    video_stream = _first_stream(streams, "video")
    audio_stream = _first_stream(streams, "audio")
    return MediaInfo(
        path=path,
        duration=_duration(payload, video_stream),
        width=_int_value(video_stream, "width"),
        height=_int_value(video_stream, "height"),
        video_codec=_str_value(video_stream, "codec_name"),
        audio_codec=_str_value(audio_stream, "codec_name"),
        has_audio=audio_stream is not None,
    )


def _first_stream(streams: list[Any], codec_type: str) -> dict[str, Any] | None:
    for stream in streams:
        if isinstance(stream, dict) and stream.get("codec_type") == codec_type:
            return stream
    return None


def _duration(payload: dict[str, Any], video_stream: dict[str, Any] | None) -> float | None:
    format_payload = payload.get("format", {})
    if isinstance(format_payload, dict):
        duration = _float_value(format_payload, "duration")
        if duration is not None:
            return duration
    return _float_value(video_stream, "duration")


def _int_value(payload: dict[str, Any] | None, key: str) -> int | None:
    if payload is None or key not in payload:
        return None
    try:
        return int(payload[key])
    except (TypeError, ValueError):
        return None


def _float_value(payload: dict[str, Any] | None, key: str) -> float | None:
    if payload is None or key not in payload:
        return None
    try:
        return float(payload[key])
    except (TypeError, ValueError):
        return None


def _str_value(payload: dict[str, Any] | None, key: str) -> str | None:
    if payload is None:
        return None
    value = payload.get(key)
    return value if isinstance(value, str) else None
