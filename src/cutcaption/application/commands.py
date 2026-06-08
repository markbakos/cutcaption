"""Command objects accepted by application services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CaptionVideoCommand:
    """Request to caption one video.

    This is intentionally small while the project foundation is being laid. Future
    use cases should extend command objects instead of passing loose dictionaries.
    """

    source: Path
    output_dir: Path | None = None
