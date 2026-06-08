"""High-level captioning orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cutcaption.chunking import chunk_words
from cutcaption.config import CutcaptionConfig
from cutcaption.exporters.ass import render_ass
from cutcaption.exporters.srt import render_srt
from cutcaption.models import VideoJob
from cutcaption.render import burn_subtitles
from cutcaption.styles import get_style
from cutcaption.transcribe import FasterWhisperTranscriber
from cutcaption.utils.paths import build_video_job, default_output_dir, discover_videos


@dataclass(frozen=True, slots=True)
class PipelineResult:
    job: VideoJob
    wrote_srt: bool
    wrote_ass: bool
    rendered: bool


class CaptionPipeline:
    def __init__(self, transcriber: FasterWhisperTranscriber | None = None) -> None:
        self._transcriber = transcriber or FasterWhisperTranscriber()

    def plan(self, input_path: Path, config: CutcaptionConfig) -> list[VideoJob]:
        videos = discover_videos(input_path)
        output_dir = config.output or default_output_dir(input_path, videos)
        return [build_video_job(video, output_dir) for video in videos]

    def run(self, input_path: Path, config: CutcaptionConfig) -> list[PipelineResult]:
        results: list[PipelineResult] = []
        for job in self.plan(input_path, config):
            job.srt_path.parent.mkdir(parents=True, exist_ok=True)
            transcript = self._transcriber.transcribe(job.source, config)
            captions = chunk_words(
                transcript.words,
                max_words=config.caption.max_words,
            )
            style = get_style(config.style)

            wrote_srt = False
            wrote_ass = False
            rendered = False

            if config.write_srt:
                job.srt_path.write_text(render_srt(captions), encoding="utf-8")
                wrote_srt = True

            if config.write_ass or config.burn:
                job.ass_path.write_text(render_ass(captions, style), encoding="utf-8")
                wrote_ass = True

            if config.burn:
                burn_subtitles(job.source, job.ass_path, job.rendered_path)
                rendered = True

            results.append(
                PipelineResult(
                    job=job,
                    wrote_srt=wrote_srt,
                    wrote_ass=wrote_ass,
                    rendered=rendered,
                )
            )
        return results
