"""Concrete file system adapter."""

from __future__ import annotations

from pathlib import Path


class LocalFileSystem:
    """File system adapter backed by ``pathlib``."""

    def exists(self, path: Path) -> bool:
        return path.exists()
