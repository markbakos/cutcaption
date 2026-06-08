"""Shared data models for caption generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"})


@dataclass(frozen=True, slots=True)
class WordTiming:
    text: str
    start: float
    end: float


@dataclass(frozen=True, slots=True)
class Caption:
    text: str
    start: float
    end: float


@dataclass(frozen=True, slots=True)
class OutputPaths:
    srt_path: Path
    ass_path: Path
    json_path: Path
    captioned_video_path: Path


@dataclass(frozen=True, slots=True)
class VideoJob:
    source: Path
    srt_path: Path
    ass_path: Path
    json_path: Path
    rendered_path: Path

    @property
    def output_paths(self) -> OutputPaths:
        return OutputPaths(
            srt_path=self.srt_path,
            ass_path=self.ass_path,
            json_path=self.json_path,
            captioned_video_path=self.rendered_path,
        )


@dataclass(frozen=True, slots=True)
class Transcript:
    words: tuple[WordTiming, ...]
    language: str | None = None
