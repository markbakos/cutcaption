"""Interfaces owned by the application layer."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileSystem(Protocol):
    """Boundary for file system operations used by use cases."""

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` exists."""
