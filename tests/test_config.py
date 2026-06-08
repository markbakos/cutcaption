from __future__ import annotations

from pathlib import Path

import pytest

from cutcaption.config import (
    BatchConfig,
    CaptionConfig,
    CutcapConfig,
    RenderConfig,
    TranscriptionConfig,
    load_config,
    write_default_config,
)


def test_config_defaults_match_mvp_contract() -> None:
    config = CutcapConfig()

    assert config.transcription == TranscriptionConfig(
        model="small",
        mode="balanced",
        language=None,
        device="auto",
        compute_type="auto",
    )
    assert config.caption == CaptionConfig(
        preset="shorts",
        style="clean",
        max_words=5,
        max_lines=2,
        min_caption_duration=0.25,
        max_caption_duration=2.5,
    )
    assert config.render == RenderConfig(burn=True, srt=True, ass=False, json=False)
    assert config.batch == BatchConfig(
        recursive=False,
        skip_existing=True,
        overwrite=False,
        jobs=1,
    )


def test_load_config_without_path_returns_defaults() -> None:
    assert load_config(None) == CutcapConfig()


def test_load_config_reads_toml_sections(tmp_path: Path) -> None:
    config_path = tmp_path / "cutcaption.toml"
    config_path.write_text(
        """
[transcription]
model = "medium"
mode = "accurate"
language = "en"
device = "cpu"
compute_type = "float32"

[caption]
preset = "youtube"
style = "bold"
max_words = 4
max_lines = 2
min_caption_duration = 0.3
max_caption_duration = 2.0

[render]
burn = false
srt = true
ass = true
json = true

[batch]
recursive = true
skip_existing = false
overwrite = true
jobs = 2
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.transcription.model == "medium"
    assert config.transcription.mode == "accurate"
    assert config.transcription.language == "en"
    assert config.caption.preset == "youtube"
    assert config.caption.style == "bold"
    assert config.caption.max_words == 4
    assert config.render.burn is False
    assert config.render.ass is True
    assert config.render.json is True
    assert config.batch.recursive is True
    assert config.batch.jobs == 2


def test_write_default_config_creates_loadable_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "cutcaption.toml"

    write_default_config(config_path)

    assert config_path.exists()
    assert load_config(config_path) == CutcapConfig()
    content = config_path.read_text(encoding="utf-8")
    assert "[transcription]" in content
    assert 'model = "small"' in content
    assert "[caption]" in content
    assert 'style = "clean"' in content


def test_config_rejects_unknown_style_with_friendly_error() -> None:
    with pytest.raises(ValueError, match="Unsupported style 'neon'.*bold.*clean.*pop"):
        CaptionConfig(style="neon")  # type: ignore[arg-type]


def test_config_rejects_unknown_preset() -> None:
    with pytest.raises(ValueError, match="Unsupported preset"):
        CaptionConfig(preset="reels")  # type: ignore[arg-type]


def test_transcription_config_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        TranscriptionConfig(mode="turbo")  # type: ignore[arg-type]


def test_caption_config_requires_positive_max_words() -> None:
    with pytest.raises(ValueError, match="max_words must be a positive integer"):
        CaptionConfig(max_words=0)


def test_batch_config_requires_positive_jobs() -> None:
    with pytest.raises(ValueError, match="jobs must be a positive integer"):
        BatchConfig(jobs=0)


def test_batch_config_rejects_conflicting_skip_and_overwrite() -> None:
    with pytest.raises(ValueError, match="skip_existing and overwrite cannot both be true"):
        BatchConfig(skip_existing=True, overwrite=True)


def test_load_config_rejects_unknown_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "cutcaption.toml"
    config_path.write_text("[caption]\nunknown = true\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown config key in caption: unknown"):
        load_config(config_path)
