"""Caption style presets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StyleConfig:
    name: str
    description: str
    font_name: str
    font_size: int
    bold: bool
    italic: bool
    primary_color: str
    outline_color: str
    back_color: str
    outline_width: int
    shadow: int
    alignment: int
    margin_v: int
    uppercase: bool
    box: bool
    highlight_current_word: bool = False
    one_word_at_a_time: bool = False


CaptionStyle = StyleConfig


STYLES: dict[str, StyleConfig] = {
    "clean": StyleConfig(
        name="clean",
        description="Readable white text with a moderate outline.",
        font_name="Arial",
        font_size=72,
        bold=True,
        italic=False,
        primary_color="&H00FFFFFF",
        outline_color="&H00000000",
        back_color="&H80000000",
        outline_width=5,
        shadow=0,
        alignment=2,
        margin_v=180,
        uppercase=False,
        box=False,
    ),
    "bold": StyleConfig(
        name="bold",
        description="Larger bold uppercase captions with a thicker outline.",
        font_name="Arial",
        font_size=84,
        bold=True,
        italic=False,
        primary_color="&H00FFFFFF",
        outline_color="&H00000000",
        back_color="&H80000000",
        outline_width=7,
        shadow=1,
        alignment=2,
        margin_v=180,
        uppercase=True,
        box=False,
    ),
    "pop": StyleConfig(
        name="pop",
        description="Big creator-style uppercase captions with thick outline and shadow.",
        font_name="Arial",
        font_size=88,
        bold=True,
        italic=False,
        primary_color="&H0000FFFF",
        outline_color="&H00000000",
        back_color="&H80000000",
        outline_width=7,
        shadow=2,
        alignment=2,
        margin_v=180,
        uppercase=True,
        box=False,
    ),
    "minimal": StyleConfig(
        name="minimal",
        description="Smaller captions with a thin outline and no uppercase transform.",
        font_name="Arial",
        font_size=58,
        bold=False,
        italic=False,
        primary_color="&H00FFFFFF",
        outline_color="&H00000000",
        back_color="&H80000000",
        outline_width=2,
        shadow=0,
        alignment=2,
        margin_v=180,
        uppercase=False,
        box=False,
    ),
    "boxed": StyleConfig(
        name="boxed",
        description="Readable text over a semi-transparent box background.",
        font_name="Arial",
        font_size=68,
        bold=True,
        italic=False,
        primary_color="&H00FFFFFF",
        outline_color="&H00000000",
        back_color="&H99000000",
        outline_width=2,
        shadow=0,
        alignment=2,
        margin_v=180,
        uppercase=False,
        box=True,
    ),
    "shorts": StyleConfig(
        name="shorts",
        description="One spoken word at a time for fast short-form captions.",
        font_name="Arial",
        font_size=90,
        bold=True,
        italic=False,
        primary_color="&H00FFFFFF",
        outline_color="&H00000000",
        back_color="&H80000000",
        outline_width=7,
        shadow=2,
        alignment=2,
        margin_v=210,
        uppercase=True,
        box=False,
        one_word_at_a_time=True,
    ),
}


def get_style(name: str) -> StyleConfig:
    key = name.lower().strip()
    try:
        return STYLES[key]
    except KeyError as exc:
        available = ", ".join(sorted(STYLES))
        raise ValueError(f"Unknown style '{name}'. Available styles: {available}.") from exc


def list_styles() -> list[StyleConfig]:
    return [STYLES[name] for name in sorted(STYLES)]
