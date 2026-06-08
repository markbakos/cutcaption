from __future__ import annotations

import pytest

from cutcaption.presentation.cli import main


def test_cli_displays_help_when_no_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Generate styled, burned-in captions" in captured.out


def test_cli_prints_plan_for_existing_video(
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"placeholder")
    output_dir = tmp_path / "captions"

    exit_code = main(["plan", str(video_path), "--output-dir", str(output_dir)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"source={video_path}" in captured.out
    assert f"output_dir={output_dir}" in captured.out
