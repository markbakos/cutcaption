"""ASS subtitle exporter."""

from __future__ import annotations

from pathlib import Path

from cutcaption.config import RenderConfig
from cutcaption.models import Caption
from cutcaption.styles import CaptionStyle, StyleConfig

PLAY_RES_X = 1080
PLAY_RES_Y = 1920
BOTTOM_CENTER_ALIGNMENT = 2
MARGIN_L = 80
MARGIN_R = 80
MARGIN_V = 180


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
                f"PlayResX: {PLAY_RES_X}",
                f"PlayResY: {PLAY_RES_Y}",
                "",
                "[V4+ Styles]",
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
                "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
                "MarginL, MarginR, MarginV, Encoding",
                f"Style: Default,{style.font_name},{style.font_size},{style.primary_color},"
                f"{style.primary_color},{style.outline_color},{style.back_color},"
                f"{-1 if style.bold else 0},0,0,0,100,100,0,0,{border_style},"
                f"{style.outline},{style.shadow},{BOTTOM_CENTER_ALIGNMENT},"
                f"{MARGIN_L},{MARGIN_R},{MARGIN_V},1",
                "",
                "[Events]",
                "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
                *events,
            ]
        )
        + "\n"
    )


def write_ass(
    captions: list[Caption],
    path: Path,
    style: StyleConfig,
    render: RenderConfig,
) -> None:
    del render
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_ass(captions, style), encoding="utf-8")


def _ass_timestamp(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    whole_seconds, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{centiseconds:02d}"


def _escape_ass(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
