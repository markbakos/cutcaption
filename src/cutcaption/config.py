"""Typed configuration models and TOML loading helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, Literal

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - covered on Python 3.10 only
    import tomli as tomllib

CaptionPreset = Literal["shorts", "youtube", "podcast", "default"]
CaptionStyleName = Literal["clean", "bold", "pop", "minimal", "boxed"]
ProcessingMode = Literal["fast", "balanced", "accurate"]

BUILT_IN_PRESETS = frozenset({"shorts", "youtube", "podcast", "default"})
BUILT_IN_STYLES = frozenset({"clean", "bold", "pop", "minimal", "boxed"})
PROCESSING_MODES = frozenset({"fast", "balanced", "accurate"})


@dataclass(frozen=True, slots=True)
class TranscriptionConfig:
    model: str = "small"
    mode: ProcessingMode = "balanced"
    language: str | None = None
    device: str = "auto"
    compute_type: str = "auto"

    def __post_init__(self) -> None:
        _validate_non_empty("model", self.model)
        _validate_choice("mode", self.mode, PROCESSING_MODES)
        _validate_non_empty("device", self.device)
        _validate_non_empty("compute_type", self.compute_type)
        if self.language is not None:
            _validate_non_empty("language", self.language)


@dataclass(frozen=True, slots=True)
class CaptionConfig:
    preset: CaptionPreset = "shorts"
    style: CaptionStyleName = "clean"
    max_words: int = 5
    max_lines: int = 2
    min_caption_duration: float = 0.25
    max_caption_duration: float = 2.5

    def __post_init__(self) -> None:
        _validate_choice("preset", self.preset, BUILT_IN_PRESETS)
        _validate_choice("style", self.style, BUILT_IN_STYLES)
        _validate_positive_int("max_words", self.max_words)
        _validate_positive_int("max_lines", self.max_lines)
        _validate_positive_number("min_caption_duration", self.min_caption_duration)
        _validate_positive_number("max_caption_duration", self.max_caption_duration)
        if self.max_caption_duration < self.min_caption_duration:
            raise ValueError("max_caption_duration must be greater than min_caption_duration.")


@dataclass(frozen=True, slots=True)
class RenderConfig:
    burn: bool = True
    srt: bool = True
    ass: bool = False
    json: bool = False


@dataclass(frozen=True, slots=True)
class BatchConfig:
    recursive: bool = False
    skip_existing: bool = True
    overwrite: bool = False
    jobs: int = 1

    def __post_init__(self) -> None:
        _validate_positive_int("jobs", self.jobs)
        if self.skip_existing and self.overwrite:
            raise ValueError("skip_existing and overwrite cannot both be true.")


@dataclass(frozen=True, slots=True)
class CutcapConfig:
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    caption: CaptionConfig = field(default_factory=CaptionConfig)
    render: RenderConfig = field(default_factory=RenderConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    output: Path | None = None

    @property
    def model(self) -> str:
        return self.transcription.model

    @property
    def mode(self) -> ProcessingMode:
        return self.transcription.mode

    @property
    def language(self) -> str | None:
        return self.transcription.language

    @property
    def device(self) -> str:
        return self.transcription.device

    @property
    def compute_type(self) -> str:
        return self.transcription.compute_type

    @property
    def preset(self) -> CaptionPreset:
        return self.caption.preset

    @property
    def style(self) -> CaptionStyleName:
        return self.caption.style

    @property
    def write_srt(self) -> bool:
        return self.render.srt

    @property
    def write_ass(self) -> bool:
        return self.render.ass

    @property
    def write_json(self) -> bool:
        return self.render.json

    @property
    def burn(self) -> bool:
        return self.render.burn


CutcaptionConfig = CutcapConfig


def load_config(path: Path | None) -> CutcapConfig:
    """Load a TOML config file, or return defaults when no path is provided."""

    if path is None:
        return CutcapConfig()

    config_path = path.expanduser()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML config '{config_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Config file '{config_path}' must contain a TOML table.")

    return _config_from_mapping(data, source=config_path)


def write_default_config(path: Path) -> None:
    """Write a readable default TOML config file."""

    config_path = path.expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(_render_default_toml(CutcapConfig()), encoding="utf-8")


def _config_from_mapping(data: dict[str, Any], *, source: Path) -> CutcapConfig:
    allowed_sections = {"transcription", "caption", "render", "batch", "output"}
    _reject_unknown_keys(data, allowed_sections, context=str(source))

    output = data.get("output")
    if output is not None and not isinstance(output, str):
        raise ValueError("Config key 'output' must be a string path.")

    return CutcapConfig(
        transcription=_section_from_mapping(
            TranscriptionConfig,
            data.get("transcription", {}),
            "transcription",
        ),
        caption=_section_from_mapping(CaptionConfig, data.get("caption", {}), "caption"),
        render=_section_from_mapping(RenderConfig, data.get("render", {}), "render"),
        batch=_section_from_mapping(BatchConfig, data.get("batch", {}), "batch"),
        output=Path(output).expanduser() if output else None,
    )


def _section_from_mapping(model_type: type[Any], data: Any, section_name: str) -> Any:
    if not isinstance(data, dict):
        raise ValueError(f"Config section '{section_name}' must be a TOML table.")

    allowed_keys = {field.name for field in fields(model_type)}
    _reject_unknown_keys(data, allowed_keys, context=section_name)
    if section_name == "transcription" and data.get("language") == "":
        data = {**data, "language": None}
    return model_type(**data)


def _reject_unknown_keys(data: dict[str, Any], allowed_keys: set[str], *, context: str) -> None:
    unknown_keys = sorted(set(data) - allowed_keys)
    if unknown_keys:
        keys = ", ".join(unknown_keys)
        allowed = ", ".join(sorted(allowed_keys))
        raise ValueError(f"Unknown config key in {context}: {keys}. Allowed keys: {allowed}.")


def _render_default_toml(config: CutcapConfig) -> str:
    data = asdict(config)
    lines = [
        "# cutcaption configuration",
        "# Defaults are tuned for short-form creator videos.",
        "",
    ]

    output = data.pop("output")
    if output is not None:
        lines.extend([f'output = "{output}"', ""])

    for section_name in ("transcription", "caption", "render", "batch"):
        section = data[section_name]
        lines.append(f"[{section_name}]")
        for key, value in section.items():
            lines.append(f"{key} = {_toml_value(value)}")
        lines.append("")

    return "\n".join(lines)


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    if value is None:
        return '"" # auto'
    if is_dataclass(value):
        raise TypeError("Nested dataclasses must be rendered as TOML sections.")
    return str(value)


def _validate_choice(name: str, value: str, allowed: frozenset[str]) -> None:
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"Unsupported {name} '{value}'. Choose one of: {choices}.")


def _validate_non_empty(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be empty.")


def _validate_positive_int(name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")


def _validate_positive_number(name: str, value: float) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive number.")
