from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from cutcaption.config import BatchConfig, CutcapConfig, RenderConfig
from cutcaption.models import JobResult, OutputPaths, Segment, Transcript, Word
from cutcaption.pipeline import process_batch, process_video


def output_paths(tmp_path: Path) -> OutputPaths:
    return OutputPaths(
        srt_path=tmp_path / "caption.srt",
        ass_path=tmp_path / "caption.ass",
        json_path=tmp_path / "caption.json",
        captioned_video_path=tmp_path / "captioned.mp4",
    )


def transcript() -> Transcript:
    words = [Word("Hello", 0.0, 0.4), Word("world", 0.4, 0.8)]
    return Transcript(
        language="en",
        duration=0.8,
        segments=[Segment("Hello world", 0.0, 0.8, words)],
    )


class FakeTranscriber:
    def transcribe(self, input_path: Path, config: CutcapConfig) -> Transcript:
        return transcript()


def test_process_video_runs_full_pipeline_with_enabled_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = output_paths(tmp_path)
    config = replace(
        CutcapConfig(),
        render=RenderConfig(burn=True, srt=True, ass=True, json=True),
        batch=BatchConfig(skip_existing=False),
    )
    write_srt = Mock()
    write_ass = Mock()
    write_json = Mock()
    burn_subtitles = Mock()
    monkeypatch.setattr("cutcaption.pipeline.FasterWhisperTranscriber", lambda: FakeTranscriber())
    monkeypatch.setattr("cutcaption.pipeline.write_srt", write_srt)
    monkeypatch.setattr("cutcaption.pipeline.write_ass", write_ass)
    monkeypatch.setattr("cutcaption.pipeline.write_json", write_json)
    monkeypatch.setattr("cutcaption.pipeline.burn_subtitles", burn_subtitles)

    result = process_video(tmp_path / "input.mp4", paths, config)

    assert result.success is True
    assert result.skipped is False
    assert result.duration == 0.8
    assert result.outputs_written == [
        paths.srt_path,
        paths.ass_path,
        paths.json_path,
        paths.captioned_video_path,
    ]
    write_srt.assert_called_once()
    write_ass.assert_called_once()
    write_json.assert_called_once()
    burn_subtitles.assert_called_once_with(
        tmp_path / "input.mp4",
        paths.ass_path,
        paths.captioned_video_path,
        overwrite=False,
    )


def test_process_video_writes_ass_when_burn_requires_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = output_paths(tmp_path)
    config = replace(
        CutcapConfig(),
        render=RenderConfig(burn=True, srt=False, ass=False, json=False),
        batch=BatchConfig(skip_existing=False),
    )
    write_ass = Mock()
    monkeypatch.setattr("cutcaption.pipeline.FasterWhisperTranscriber", lambda: FakeTranscriber())
    monkeypatch.setattr("cutcaption.pipeline.write_ass", write_ass)
    monkeypatch.setattr("cutcaption.pipeline.burn_subtitles", Mock())

    result = process_video(tmp_path / "input.mp4", paths, config)

    assert result.success is True
    assert paths.ass_path in result.outputs_written
    write_ass.assert_called_once()


def test_process_video_skips_existing_requested_output_before_transcription(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = output_paths(tmp_path)
    paths.srt_path.write_text("existing", encoding="utf-8")
    transcriber_factory = Mock(return_value=FakeTranscriber())
    monkeypatch.setattr("cutcaption.pipeline.FasterWhisperTranscriber", transcriber_factory)

    result = process_video(tmp_path / "input.mp4", paths, CutcapConfig())

    assert result.success is True
    assert result.skipped is True
    assert result.outputs_written == []
    transcriber_factory.assert_not_called()


def test_process_video_reports_failure_when_existing_output_is_not_skipped(
    tmp_path: Path,
) -> None:
    paths = output_paths(tmp_path)
    paths.srt_path.write_text("existing", encoding="utf-8")
    config = replace(CutcapConfig(), batch=BatchConfig(skip_existing=False))

    result = process_video(tmp_path / "input.mp4", paths, config)

    assert result.success is False
    assert result.skipped is False
    assert result.error_message is not None
    assert "Output already exists" in result.error_message


def test_process_batch_continues_after_per_file_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"

    def fake_process(input_path: Path, paths: OutputPaths, config: CutcapConfig) -> JobResult:
        _ = paths, config
        if input_path == first:
            return JobResult(input_path=input_path, success=False, outputs_written=[], error_message="failed")
        return JobResult(input_path=input_path, success=True, outputs_written=[])

    monkeypatch.setattr("cutcaption.pipeline.process_video", fake_process)

    result = process_batch([first, second], CutcapConfig(), tmp_path / "out")

    assert result.total == 2
    assert result.succeeded == 1
    assert result.failed == 1
    assert result.skipped == 0
    assert [job.input_path for job in result.results] == [first, second]
