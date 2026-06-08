"""Application use cases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cutcaption.application.commands import CaptionVideoCommand
from cutcaption.application.ports import FileSystem


@dataclass(frozen=True, slots=True)
class CaptionPlan:
    """Validated plan for a future captioning run."""

    source: Path
    output_dir: Path


class PlanCaptionRun:
    """Validate captioning inputs without performing media work."""

    def __init__(self, file_system: FileSystem) -> None:
        self._file_system = file_system

    def execute(self, command: CaptionVideoCommand) -> CaptionPlan:
        source = command.source.expanduser()
        if not self._file_system.exists(source):
            raise FileNotFoundError(f"Video does not exist: {source}")

        output_dir = command.output_dir.expanduser() if command.output_dir else source.parent
        return CaptionPlan(source=source, output_dir=output_dir)
