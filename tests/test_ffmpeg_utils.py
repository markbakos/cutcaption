from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from cutcaption.utils import ffmpeg
from cutcaption.utils.ffmpeg import FfmpegCommandError, FfmpegNotFoundError, probe_media, run_command


def test_check_ffmpeg_and_ffprobe_use_path_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ffmpeg.shutil, "which", lambda name: f"/usr/bin/{name}")

    assert ffmpeg.check_ffmpeg() is True
    assert ffmpeg.check_ffprobe() is True


def test_run_command_raises_friendly_error_for_missing_binary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_binary(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("missing")

    monkeypatch.setattr(ffmpeg.subprocess, "run", missing_binary)

    with pytest.raises(FfmpegNotFoundError, match="Required executable not found"):
        run_command(["ffmpeg", "-version"])


def test_run_command_captures_stderr_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    completed = subprocess.CompletedProcess(
        args=["ffmpeg"],
        returncode=1,
        stdout="",
        stderr="bad filter",
    )
    run = Mock(return_value=completed)
    monkeypatch.setattr(ffmpeg.subprocess, "run", run)

    with pytest.raises(FfmpegCommandError, match="bad filter"):
        run_command(["ffmpeg"])

    run.assert_called_once_with(["ffmpeg"], check=False, capture_output=True, text=True)


def test_probe_media_parses_ffprobe_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ffmpeg, "check_ffprobe", lambda: True)
    monkeypatch.setattr(
        ffmpeg,
        "run_command",
        Mock(
            return_value=subprocess.CompletedProcess(
                args=["ffprobe"],
                returncode=0,
                stdout=(
                    '{"format":{"duration":"12.5"},"streams":['
                    '{"codec_type":"video","codec_name":"h264","width":1080,"height":1920},'
                    '{"codec_type":"audio","codec_name":"aac"}'
                    "]}"
                ),
                stderr="",
            )
        ),
    )

    info = probe_media(Path("/tmp/source video.mp4"))

    assert info.path == Path("/tmp/source video.mp4")
    assert info.duration == 12.5
    assert info.width == 1080
    assert info.height == 1920
    assert info.video_codec == "h264"
    assert info.audio_codec == "aac"
    assert info.has_audio is True


def test_probe_media_raises_when_ffprobe_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ffmpeg, "check_ffprobe", lambda: False)

    with pytest.raises(FfmpegNotFoundError, match="ffprobe not found"):
        probe_media(Path("input.mp4"))
