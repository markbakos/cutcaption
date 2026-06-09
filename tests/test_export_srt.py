from __future__ import annotations

from pathlib import Path

from cutcaption.exporters.srt import render_srt, write_srt
from cutcaption.models import Caption


def test_render_srt_formats_numbered_cues() -> None:
    output = render_srt([Caption("Hello world", 0.0, 1.25), Caption("Next", 61.0, 62.5)])

    assert output == (
        "1\n"
        "00:00:00,000 --> 00:00:01,250\n"
        "Hello world\n"
        "\n"
        "2\n"
        "00:01:01,000 --> 00:01:02,500\n"
        "Next\n"
    )


def test_write_srt_creates_valid_srt_file(tmp_path: Path) -> None:
    path = tmp_path / "sample.srt"

    write_srt([Caption("Hello world", 0.0, 1.25), Caption("Next caption", 61.0, 62.5)], path)

    assert path.read_text(encoding="utf-8") == (
        "1\n"
        "00:00:00,000 --> 00:00:01,250\n"
        "Hello world\n"
        "\n"
        "2\n"
        "00:01:01,000 --> 00:01:02,500\n"
        "Next caption\n"
    )


def test_render_srt_wraps_text_when_it_fits_two_lines() -> None:
    output = render_srt(
        [
            Caption(
                "This is a longer caption that should wrap into two readable subtitle lines",
                0.0,
                2.0,
            )
        ]
    )

    assert output.count("\n") == 4
    assert "readable subtitle lines\n" in output
