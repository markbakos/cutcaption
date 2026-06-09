"""Shared data models for caption generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"})


@dataclass(frozen=True, slots=True)
class Word:
    text: str
    start: float
    end: float
    probability: float | None = None


WordTiming = Word


@dataclass(frozen=True, slots=True)
class Segment:
    text: str
    start: float
    end: float
    words: list[Word]


@dataclass(frozen=True, slots=True)
class Caption:
    text: str
    start: float
    end: float
    words: list[Word] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class OutputPaths:
    srt_path: Path
    ass_path: Path
    json_path: Path
    captioned_video_path: Path


@dataclass(frozen=True, slots=True)
class JobResult:
    input_path: Path
    success: bool
    outputs_written: list[Path]
    skipped: bool = False
    error_message: str | None = None
    duration: float | None = None


@dataclass(frozen=True, slots=True)
class BatchResult:
    total: int
    succeeded: int
    failed: int
    skipped: int
    results: list[JobResult]


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
    language: str | None = None
    duration: float | None = None
    segments: list[Segment] | None = None

    @property
    def words(self) -> tuple[Word, ...]:
        if self.segments is None:
            return ()
        return tuple(word for segment in self.segments for word in segment.words)
