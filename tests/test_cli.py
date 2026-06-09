from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from cutcaption.models import VideoJob


def test_cli_dry_run_does_not_process(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pytest.importorskip("typer")
    from cutcaption.cli import main

    input_path = tmp_path / "input.mp4"
    input_path.write_text("video", encoding="utf-8")
    process_batch = Mock()
    monkeypatch.setattr(
        "cutcaption.cli.plan_jobs",
        Mock(
            return_value=[
                VideoJob(
                    source=input_path,
                    srt_path=tmp_path / "input.srt",
                    ass_path=tmp_path / "input.ass",
                    json_path=tmp_path / "input.json",
                    rendered_path=tmp_path / "input_captioned.mp4",
                )
            ]
        ),
    )
    monkeypatch.setattr("cutcaption.cli.process_batch", process_batch)

    monkeypatch.setattr("sys.argv", ["cutcaption", str(input_path), "--dry-run"])

    main()
    process_batch.assert_not_called()
