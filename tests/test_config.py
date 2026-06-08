from __future__ import annotations

import pytest

from cutcaption.config import CutcaptionConfig


def test_config_defaults_match_mvp_contract() -> None:
    config = CutcaptionConfig()

    assert config.preset == "shorts"
    assert config.style == "clean"
    assert config.model == "small"
    assert config.mode == "balanced"
    assert config.write_srt is True
    assert config.burn is True


def test_config_rejects_unknown_style() -> None:
    with pytest.raises(ValueError, match="Unsupported style"):
        CutcaptionConfig(style="neon")  # type: ignore[arg-type]
