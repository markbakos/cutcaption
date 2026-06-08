from __future__ import annotations

from pathlib import Path

import pytest

from cutcaption.utils.paths import (
    build_output_paths,
    build_video_job,
    discover_inputs,
    folder_output_dir,
    is_video_file,
)


def test_is_video_file_accepts_supported_extensions_case_insensitively(tmp_path: Path) -> None:
    video = tmp_path / "clip.MP4"
    video.write_bytes(b"video")

    assert is_video_file(video) is True


def test_is_video_file_rejects_non_files_and_unsupported_extensions(tmp_path: Path) -> None:
    text = tmp_path / "clip.txt"
    text.write_text("nope", encoding="utf-8")

    assert is_video_file(text) is False
    assert is_video_file(tmp_path) is False


def test_discover_inputs_processes_one_supported_file(tmp_path: Path) -> None:
    video = tmp_path / "clip.mov"
    video.write_bytes(b"video")

    assert discover_inputs(video) == [video]


def test_discover_inputs_rejects_unsupported_file_with_friendly_error(tmp_path: Path) -> None:
    text = tmp_path / "clip.txt"
    text.write_text("nope", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file type: clip.txt"):
        discover_inputs(text)


def test_discover_inputs_sorts_non_recursive_folder_videos(tmp_path: Path) -> None:
    second = tmp_path / "b.mov"
    first = tmp_path / "a.mp4"
    nested = tmp_path / "nested"
    nested.mkdir()
    nested_video = nested / "nested.mp4"
    ignored = tmp_path / "notes.txt"
    second.write_bytes(b"video")
    first.write_bytes(b"video")
    nested_video.write_bytes(b"video")
    ignored.write_text("nope", encoding="utf-8")

    assert discover_inputs(tmp_path, recursive=False) == [first, second]


def test_discover_inputs_finds_nested_videos_when_recursive(tmp_path: Path) -> None:
    root_video = tmp_path / "root.mp4"
    nested = tmp_path / "nested"
    nested.mkdir()
    nested_video = nested / "nested.webm"
    root_video.write_bytes(b"video")
    nested_video.write_bytes(b"video")

    assert discover_inputs(tmp_path, recursive=True) == [nested_video, root_video]


def test_discover_inputs_empty_folder_has_friendly_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="No supported video files found"):
        discover_inputs(tmp_path)


def test_build_output_paths_defaults_to_source_directory_and_creates_it(tmp_path: Path) -> None:
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")

    output_paths = build_output_paths(video, output_dir=None)

    assert output_paths.srt_path == tmp_path / "video.srt"
    assert output_paths.ass_path == tmp_path / "video.ass"
    assert output_paths.json_path == tmp_path / "video.json"
    assert output_paths.captioned_video_path == tmp_path / "video_captioned.mp4"


def test_build_output_paths_uses_output_directory_and_creates_it(tmp_path: Path) -> None:
    output_dir = tmp_path / "captioned"
    video = tmp_path / "source" / "my.video.mp4"
    video.parent.mkdir()
    video.write_bytes(b"video")

    output_paths = build_output_paths(video, output_dir=output_dir)

    assert output_dir.exists()
    assert output_paths.srt_path == output_dir / "my.video.srt"
    assert output_paths.ass_path == output_dir / "my.video.ass"
    assert output_paths.json_path == output_dir / "my.video.json"
    assert output_paths.captioned_video_path == output_dir / "my.video_captioned.mp4"


def test_folder_output_dir_defaults_to_captioned_for_folder(tmp_path: Path) -> None:
    assert folder_output_dir(tmp_path, None) == tmp_path / "captioned"


def test_build_video_job_uses_output_paths(tmp_path: Path) -> None:
    job = build_video_job(tmp_path / "video.mp4", tmp_path / "out")

    assert job.srt_path == tmp_path / "out" / "video.srt"
    assert job.ass_path == tmp_path / "out" / "video.ass"
    assert job.json_path == tmp_path / "out" / "video.json"
    assert job.rendered_path == tmp_path / "out" / "video_captioned.mp4"
