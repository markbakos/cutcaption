"""High-level captioning orchestration."""

from __future__ import annotations

from pathlib import Path

from cutcaption.chunking import build_captions
from cutcaption.config import CutcaptionConfig
from cutcaption.exporters.ass import write_ass
from cutcaption.exporters.json import write_json
from cutcaption.exporters.srt import write_srt
from cutcaption.models import BatchResult, JobResult, OutputPaths, VideoJob
from cutcaption.render import OutputExistsError, burn_subtitles
from cutcaption.styles import get_style
from cutcaption.transcribe import FasterWhisperTranscriber
from cutcaption.utils.paths import (
    build_output_paths,
    build_video_job,
    discover_inputs,
    folder_output_dir,
)


def process_video(
    input_path: Path,
    output_paths: OutputPaths,
    config: CutcaptionConfig,
) -> JobResult:
    """Transcribe, caption, export, and optionally render one video."""

    requested_outputs = _requested_outputs(output_paths, config)
    existing_outputs = [path for path in requested_outputs if path.exists()]
    if existing_outputs and config.batch.skip_existing and not config.batch.overwrite:
        return JobResult(
            input_path=input_path,
            success=True,
            outputs_written=[],
            skipped=True,
            duration=None,
        )

    outputs_written: list[Path] = []
    try:
        _ensure_outputs_writable(requested_outputs, config)
        transcript = FasterWhisperTranscriber().transcribe(input_path, config)
        captions = build_captions(transcript, config.caption)
        style = get_style(config.style)

        if config.write_srt:
            write_srt(captions, output_paths.srt_path)
            outputs_written.append(output_paths.srt_path)

        if config.write_ass or config.burn:
            write_ass(captions, output_paths.ass_path, style, config.render)
            outputs_written.append(output_paths.ass_path)

        if config.write_json:
            write_json(transcript, captions, output_paths.json_path)
            outputs_written.append(output_paths.json_path)

        if config.burn:
            burn_subtitles(
                input_path,
                output_paths.ass_path,
                output_paths.captioned_video_path,
                overwrite=config.batch.overwrite,
            )
            outputs_written.append(output_paths.captioned_video_path)

        return JobResult(
            input_path=input_path,
            success=True,
            outputs_written=outputs_written,
            duration=transcript.duration,
        )
    except Exception as exc:
        return JobResult(
            input_path=input_path,
            success=False,
            outputs_written=outputs_written,
            error_message=str(exc),
        )


def process_batch(
    input_paths: list[Path],
    config: CutcaptionConfig,
    output_dir: Path | None,
) -> BatchResult:
    """Process videos sequentially.

    TODO: Use config.batch.jobs for parallel processing once shared model loading
    and progress reporting are coordinated.
    """

    results: list[JobResult] = []
    for input_path in input_paths:
        output_paths = build_output_paths(input_path, output_dir)
        results.append(process_video(input_path, output_paths, config))

    succeeded = sum(1 for result in results if result.success and not result.skipped)
    failed = sum(1 for result in results if not result.success)
    skipped = sum(1 for result in results if result.skipped)
    return BatchResult(
        total=len(results),
        succeeded=succeeded,
        failed=failed,
        skipped=skipped,
        results=results,
    )


def plan_jobs(input_path: Path, config: CutcaptionConfig) -> list[VideoJob]:
    videos = discover_inputs(input_path, recursive=config.batch.recursive)
    output_dir = folder_output_dir(input_path, config.output)
    return [build_video_job(video, output_dir) for video in videos]


class CaptionPipeline:
    """Compatibility wrapper around the function-based pipeline API."""

    def plan(self, input_path: Path, config: CutcaptionConfig) -> list[VideoJob]:
        return plan_jobs(input_path, config)

    def run(self, input_path: Path, config: CutcaptionConfig) -> list[JobResult]:
        jobs = self.plan(input_path, config)
        output_dir = folder_output_dir(input_path, config.output)
        return process_batch([job.source for job in jobs], config, output_dir).results


def _requested_outputs(output_paths: OutputPaths, config: CutcaptionConfig) -> list[Path]:
    outputs: list[Path] = []
    if config.write_srt:
        outputs.append(output_paths.srt_path)
    if config.write_ass or config.burn:
        outputs.append(output_paths.ass_path)
    if config.write_json:
        outputs.append(output_paths.json_path)
    if config.burn:
        outputs.append(output_paths.captioned_video_path)
    return outputs


def _ensure_outputs_writable(outputs: list[Path], config: CutcaptionConfig) -> None:
    if config.batch.overwrite:
        return
    for path in outputs:
        if path.exists():
            raise OutputExistsError(
                f"Output already exists: {path}. Use overwrite or skip existing outputs."
            )
