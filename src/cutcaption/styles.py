"""Caption style presets."""

from __future__ import annotations

from dataclasses import dataclass

from cutcaption.config import CaptionStyleName


@dataclass(frozen=True, slots=True)
class CaptionStyle:
    name: CaptionStyleName
    font_name: str
    font_size: int
    primary_color: str
    outline_color: str
    back_color: str
    bold: bool
    outline: int
    shadow: int
    boxed: bool = False


StyleConfig = CaptionStyle


STYLES: dict[CaptionStyleName, CaptionStyle] = {
    "clean": CaptionStyle(
        "clean", "Arial", 72, "&H00FFFFFF", "&H00000000", "&H80000000", True, 5, 0
    ),
    "bold": CaptionStyle(
        "bold", "Arial", 84, "&H00FFFFFF", "&H00000000", "&H80000000", True, 7, 1
    ),
    "pop": CaptionStyle(
        "pop", "Arial", 82, "&H0000FFFF", "&H00000000", "&H80000000", True, 6, 2
    ),
    "minimal": CaptionStyle(
        "minimal", "Arial", 58, "&H00FFFFFF", "&H00000000", "&H80000000", False, 2, 0
    ),
    "boxed": CaptionStyle(
        "boxed", "Arial", 68, "&H00FFFFFF", "&H00000000", "&H99000000", True, 2, 0, True
    ),
}


def get_style(name: CaptionStyleName) -> CaptionStyle:
    try:
        return STYLES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown style '{name}'.") from exc
