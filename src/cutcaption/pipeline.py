"""High-level captioning orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cutcaption.chunking import build_captions
from cutcaption.config import CutcaptionConfig
from cutcaption.exporters.ass import write_ass
from cutcaption.exporters.json import write_json
from cutcaption.exporters.srt import write_srt
from cutcaption.models import VideoJob
from cutcaption.render import burn_subtitles
from cutcaption.styles import get_style
from cutcaption.transcribe import FasterWhisperTranscriber
from cutcaption.utils.paths import build_video_job, discover_inputs, folder_output_dir


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
        videos = discover_inputs(input_path, recursive=config.batch.recursive)
        output_dir = folder_output_dir(input_path, config.output)
        return [build_video_job(video, output_dir) for video in videos]

    def run(self, input_path: Path, config: CutcaptionConfig) -> list[PipelineResult]:
        results: list[PipelineResult] = []
        for job in self.plan(input_path, config):
            job.srt_path.parent.mkdir(parents=True, exist_ok=True)
            transcript = self._transcriber.transcribe(job.source, config)
            captions = build_captions(transcript, config.caption)
            style = get_style(config.style)

            wrote_srt = False
            wrote_ass = False
            rendered = False

            if config.write_srt:
                write_srt(captions, job.srt_path)
                wrote_srt = True

            if config.write_ass or config.burn:
                write_ass(captions, job.ass_path, style, config.render)
                wrote_ass = True

            if config.write_json:
                write_json(transcript, captions, job.json_path)

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
