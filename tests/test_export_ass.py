from __future__ import annotations

from pathlib import Path

from cutcaption.config import RenderConfig
from cutcaption.exporters.ass import render_ass, write_ass
from cutcaption.models import Caption
from cutcaption.styles import get_style


def test_render_ass_includes_style_and_dialogue() -> None:
    output = render_ass([Caption("Hello {world}", 0.0, 1.2)], get_style("clean"))

    assert "[V4+ Styles]" in output
    assert "Style: Default,Arial,72" in output
    assert "Dialogue: 0,0:00:00.00,0:00:01.20,Default" in output
    assert r"Hello \{world\}" in output


def test_render_ass_uses_bottom_center_style_values() -> None:
    output = render_ass([Caption("Hello", 0.0, 1.2)], get_style("boxed"))

    assert "PlayResX: 1080" in output
    assert "PlayResY: 1920" in output
    assert "Style: Default,Arial,68" in output
    assert ",3,2,0,2,80,80,180,1" in output


def test_write_ass_creates_style_and_dialogue_file(tmp_path: Path) -> None:
    path = tmp_path / "sample.ass"

    write_ass([Caption("Hello", 0.0, 1.2)], path, get_style("pop"), RenderConfig())

    output = path.read_text(encoding="utf-8")
    assert "[V4+ Styles]" in output
    assert "Style: Default,Arial,82" in output
    assert "Dialogue: 0,0:00:00.00,0:00:01.20,Default" in output
