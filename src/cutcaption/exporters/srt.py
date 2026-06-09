"""SRT subtitle exporter."""

from __future__ import annotations

import textwrap
from pathlib import Path

from cutcaption.models import Caption

DEFAULT_MAX_LINES = 2
DEFAULT_LINE_WIDTH = 42


def render_srt(captions: list[Caption] | tuple[Caption, ...]) -> str:
    blocks = []
    for index, caption in enumerate(captions, start=1):
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{_srt_timestamp(caption.start)} --> {_srt_timestamp(caption.end)}",
                    _wrap_caption_text(caption.text),
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def write_srt(captions: list[Caption], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_srt(captions), encoding="utf-8")


def _srt_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def _wrap_caption_text(
    text: str,
    *,
    max_lines: int = DEFAULT_MAX_LINES,
    line_width: int = DEFAULT_LINE_WIDTH,
) -> str:
    clean = " ".join(text.split())
    if not clean:
        return ""

    wrapped = textwrap.wrap(
        clean,
        width=line_width,
        break_long_words=False,
        break_on_hyphens=False,
    )
    if len(wrapped) <= max_lines:
        return "\n".join(wrapped)

    return clean
