from __future__ import annotations

from pathlib import Path

import pytest

from cutcaption.application.commands import CaptionVideoCommand
from cutcaption.application.use_cases import PlanCaptionRun


class StubFileSystem:
    def __init__(self, existing_paths: set[Path]) -> None:
        self._existing_paths = existing_paths

    def exists(self, path: Path) -> bool:
        return path in self._existing_paths


def test_plan_caption_run_defaults_output_dir_to_source_parent() -> None:
    source = Path("videos/clip.mp4")
    use_case = PlanCaptionRun(StubFileSystem({source}))

    plan = use_case.execute(CaptionVideoCommand(source=source))

    assert plan.source == source
    assert plan.output_dir == Path("videos")


def test_plan_caption_run_rejects_missing_source() -> None:
    use_case = PlanCaptionRun(StubFileSystem(set()))

    with pytest.raises(FileNotFoundError, match="Video does not exist"):
        use_case.execute(CaptionVideoCommand(source=Path("missing.mp4")))
