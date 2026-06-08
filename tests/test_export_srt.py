from __future__ import annotations

from cutcaption.exporters.srt import render_srt
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
