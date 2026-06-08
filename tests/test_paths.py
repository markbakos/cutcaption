from __future__ import annotations

from pathlib import Path

import pytest

from cutcaption.utils.paths import build_video_job, default_output_dir, discover_videos


def test_discover_videos_accepts_supported_file(tmp_path: Path) -> None:
    video = tmp_path / "clip.MP4"
    video.write_bytes(b"video")

    assert discover_videos(video) == [video]


def test_discover_videos_sorts_folder_videos(tmp_path: Path) -> None:
    second = tmp_path / "b.mov"
    first = tmp_path / "a.mp4"
    ignored = tmp_path / "notes.txt"
    second.write_bytes(b"video")
    first.write_bytes(b"video")
    ignored.write_text("nope", encoding="utf-8")

    assert discover_videos(tmp_path) == [first, second]


def test_discover_videos_rejects_unsupported_file(tmp_path: Path) -> None:
    text = tmp_path / "clip.txt"
    text.write_text("nope", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported video extension"):
        discover_videos(text)


def test_default_output_dir_for_folder_is_captioned(tmp_path: Path) -> None:
    video = tmp_path / "clip.mp4"

    assert default_output_dir(tmp_path, [video]) == tmp_path / "captioned"


def test_build_video_job_uses_expected_names(tmp_path: Path) -> None:
    job = build_video_job(tmp_path / "video.mp4", tmp_path / "out")

    assert job.srt_path == tmp_path / "out" / "video.srt"
    assert job.ass_path == tmp_path / "out" / "video.ass"
    assert job.rendered_path == tmp_path / "out" / "video_captioned.mp4"
