from __future__ import annotations

from cutcaption.exporters.ass import render_ass
from cutcaption.models import Caption
from cutcaption.styles import get_style


def test_render_ass_includes_style_and_dialogue() -> None:
    output = render_ass([Caption("Hello {world}", 0.0, 1.2)], get_style("clean"))

    assert "[V4+ Styles]" in output
    assert "Style: Default,Arial,72" in output
    assert "Dialogue: 0,0:00:00.00,0:00:01.20,Default" in output
    assert r"Hello \{world\}" in output
