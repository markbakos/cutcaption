"""SRT subtitle exporter."""

from __future__ import annotations

from cutcaption.models import Caption


def render_srt(captions: list[Caption] | tuple[Caption, ...]) -> str:
    blocks = []
    for index, caption in enumerate(captions, start=1):
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{_srt_timestamp(caption.start)} --> {_srt_timestamp(caption.end)}",
                    caption.text,
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _srt_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"
