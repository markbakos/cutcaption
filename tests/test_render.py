from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from cutcaption.render import (
    OutputExistsError,
    _burn_subtitles_command,
    _escape_subtitle_filter_path,
    burn_subtitles,
)
from cutcaption.utils.ffmpeg import FfmpegNotFoundError


def test_burn_subtitles_command_uses_ass_filter_and_preserves_audio() -> None:
    command = _burn_subtitles_command(
        Path("/tmp/input video.mp4"),
        Path("/tmp/captions file.ass"),
        Path("/tmp/output video.mp4"),
        overwrite=True,
    )

    assert command[:5] == ["ffmpeg", "-y", "-i", "/tmp/input video.mp4", "-vf"]
    assert command[5] == "subtitles=filename='/tmp/captions file.ass'"
    assert "-c:v" in command
    assert "libx264" in command
    assert "-crf" in command
    assert "18" in command
    assert "-preset" in command
    assert "medium" in command
    assert command[command.index("-map") + 1] == "0:v:0"
    assert "0:a?" in command
    assert command[-3:] == ["-c:a", "copy", "/tmp/output video.mp4"]


def test_burn_subtitles_raises_when_ffmpeg_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("cutcaption.render.check_ffmpeg", lambda: False)

    with pytest.raises(FfmpegNotFoundError, match="ffmpeg not found"):
        burn_subtitles(tmp_path / "input.mp4", tmp_path / "captions.ass", tmp_path / "out.mp4")


def test_burn_subtitles_raises_when_output_exists_without_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "already exists.mp4"
    output_path.write_text("existing", encoding="utf-8")
    run_command = Mock()
    monkeypatch.setattr("cutcaption.render.check_ffmpeg", lambda: True)
    monkeypatch.setattr("cutcaption.render.run_command", run_command)

    with pytest.raises(OutputExistsError, match="Output already exists"):
        burn_subtitles(tmp_path / "input.mp4", tmp_path / "captions.ass", output_path)

    run_command.assert_not_called()


def test_burn_subtitles_calls_ffmpeg_command_with_spaces(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_command = Mock()
    monkeypatch.setattr("cutcaption.render.check_ffmpeg", lambda: True)
    monkeypatch.setattr("cutcaption.render.run_command", run_command)

    burn_subtitles(
        tmp_path / "input video.mp4",
        tmp_path / "styled captions.ass",
        tmp_path / "rendered video.mp4",
        overwrite=True,
    )

    command = run_command.call_args.args[0]
    assert command[0] == "ffmpeg"
    assert command[1] == "-y"
    assert str(tmp_path / "input video.mp4") in command
    assert command[-1] == str(tmp_path / "rendered video.mp4")
    assert "styled captions.ass" in command[5]


def test_subtitle_filter_path_escaping() -> None:
    escaped = _escape_subtitle_filter_path(Path("/tmp/a dir/cap'tion:one,two[3].ass"))

    assert escaped == r"/tmp/a dir/cap\'tion\:one\,two\[3\].ass"
