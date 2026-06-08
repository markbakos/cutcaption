"""ASS subtitle exporter."""

from __future__ import annotations

from cutcaption.models import Caption
from cutcaption.styles import CaptionStyle


def render_ass(captions: list[Caption] | tuple[Caption, ...], style: CaptionStyle) -> str:
    events = [
        "Dialogue: 0,"
        f"{_ass_timestamp(caption.start)},{_ass_timestamp(caption.end)},Default,,0,0,0,,"
        f"{_escape_ass(caption.text)}"
        for caption in captions
    ]
    border_style = 3 if style.boxed else 1

    return (
        "\n".join(
            [
                "[Script Info]",
                "ScriptType: v4.00+",
                "WrapStyle: 2",
                "ScaledBorderAndShadow: yes",
                "PlayResX: 1080",
                "PlayResY: 1920",
                "",
                "[V4+ Styles]",
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
                "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
                "MarginL, MarginR, MarginV, Encoding",
                f"Style: Default,{style.font_name},{style.font_size},{style.primary_color},"
                f"{style.primary_color},{style.outline_color},{style.back_color},"
                f"{-1 if style.bold else 0},0,0,0,100,100,0,0,{border_style},"
                f"{style.outline},{style.shadow},5,80,80,280,1",
                "",
                "[Events]",
                "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
                *events,
            ]
        )
        + "\n"
    )


def _ass_timestamp(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    whole_seconds, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{centiseconds:02d}"


def _escape_ass(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
