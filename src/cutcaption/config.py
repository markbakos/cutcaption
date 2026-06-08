"""Validated user-facing configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

CaptionPreset = Literal["shorts"]
CaptionStyleName = Literal["clean", "bold", "pop", "minimal", "boxed"]
ProcessingMode = Literal["fast", "balanced", "accurate"]


@dataclass(frozen=True, slots=True)
class CutcaptionConfig:
    preset: CaptionPreset = "shorts"
    style: CaptionStyleName = "clean"
    model: str = "small"
    mode: ProcessingMode = "balanced"
    language: str | None = None
    output: Path | None = None
    write_srt: bool = True
    write_ass: bool = False
    burn: bool = True

    def __post_init__(self) -> None:
        _validate_choice("preset", self.preset, {"shorts"})
        _validate_choice("style", self.style, {"clean", "bold", "pop", "minimal", "boxed"})
        _validate_choice("mode", self.mode, {"fast", "balanced", "accurate"})
        if not self.model.strip():
            raise ValueError("Model cannot be empty.")
        if self.language is not None and not self.language.strip():
            raise ValueError("Language cannot be blank. Omit it to use automatic detection.")


def _validate_choice(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"Unsupported {name} '{value}'. Choose one of: {choices}.")
