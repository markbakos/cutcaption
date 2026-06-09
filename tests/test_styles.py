from __future__ import annotations

import pytest

from cutcaption.exporters.ass import render_ass
from cutcaption.models import Caption, Word
from cutcaption.styles import get_style, list_styles


def test_valid_styles_load() -> None:
    styles = {style.name: style for style in list_styles()}

    assert {"clean", "bold", "pop", "minimal", "boxed", "shorts"} <= set(styles)
    assert styles["clean"].description
    assert styles["shorts"].one_word_at_a_time is True


def test_invalid_style_errors() -> None:
    with pytest.raises(ValueError, match="Unknown style 'neon'.*boxed.*shorts"):
        get_style("neon")


def test_style_fields_are_sane() -> None:
    for style in list_styles():
        assert style.name
        assert style.description
        assert style.font_name
        assert style.font_size > 0
        assert style.outline_width >= 0
        assert style.shadow >= 0
        assert style.alignment in {1, 2, 3, 4, 5, 6, 7, 8, 9}
        assert style.margin_v >= 0
        assert style.primary_color.startswith("&H")
        assert style.outline_color.startswith("&H")
        assert style.back_color.startswith("&H")
        assert style.highlight_current_word is False


def test_cutcaption_styles_displays_requested_table() -> None:
    pytest.importorskip("typer")
    from typer.testing import CliRunner

    from cutcaption.cli import app

    result = CliRunner().invoke(app, ["styles"])

    assert result.exit_code == 0
    assert "Caption styles" in result.output
    assert "Name" in result.output
    assert "Description" in result.output
    assert "Uppercase" in result.output
    assert "Font size" in result.output
    assert "Box" in result.output
    assert "shorts" in result.output


def test_ass_exporter_uses_style_config_uppercase_and_word_events() -> None:
    output = render_ass(
        [
            Caption(
                "hello world",
                0.0,
                1.0,
                words=[Word("hello", 0.0, 0.4), Word("world", 0.4, 1.0)],
            )
        ],
        get_style("shorts"),
    )

    assert "Style: Default,Arial,90" in output
    assert "Dialogue: 0,0:00:00.00,0:00:00.40,Default,,0,0,0,,HELLO" in output
    assert "Dialogue: 0,0:00:00.40,0:00:01.00,Default,,0,0,0,,WORLD" in output
    assert "hello world" not in output
