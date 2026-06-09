"""ASS subtitle exporter."""

from __future__ import annotations

from pathlib import Path

from cutcaption.config import RenderConfig
from cutcaption.models import Caption, Word
from cutcaption.styles import CaptionStyle, StyleConfig

PLAY_RES_X = 1080
PLAY_RES_Y = 1920
MARGIN_L = 80
MARGIN_R = 80


def render_ass(captions: list[Caption] | tuple[Caption, ...], style: CaptionStyle) -> str:
    events = [
        "Dialogue: 0,"
        f"{_ass_timestamp(start)},{_ass_timestamp(end)},Default,,0,0,0,,"
        f"{_escape_ass(_style_text(text, style))}"
        for text, start, end in _iter_events(captions, style)
    ]
    border_style = 3 if style.box else 1

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
                f"{-1 if style.bold else 0},{-1 if style.italic else 0},0,0,100,100,0,0,"
                f"{border_style},{style.outline_width},{style.shadow},{style.alignment},"
                f"{MARGIN_L},{MARGIN_R},{style.margin_v},1",
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


def _iter_events(
    captions: list[Caption] | tuple[Caption, ...],
    style: CaptionStyle,
) -> list[tuple[str, float, float]]:
    events: list[tuple[str, float, float]] = []
    for caption in captions:
        if style.one_word_at_a_time and caption.words:
            events.extend(_word_events(caption.words))
        else:
            events.append((caption.text, caption.start, caption.end))
    return events


def _word_events(words: list[Word]) -> list[tuple[str, float, float]]:
    return [(word.text, word.start, word.end) for word in words]


def _style_text(text: str, style: CaptionStyle) -> str:
    return text.upper() if style.uppercase else text


def _ass_timestamp(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    whole_seconds, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{centiseconds:02d}"


def _escape_ass(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
