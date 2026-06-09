from __future__ import annotations

import json
from pathlib import Path

from cutcaption.exporters.json import render_json, write_json
from cutcaption.models import Caption, Segment, Transcript, Word


def sample_transcript() -> Transcript:
    words = [Word("Hello", 0.0, 0.4, 0.98), Word("world", 0.4, 0.8, 0.95)]
    return Transcript(
        language="en",
        duration=0.8,
        segments=[Segment("Hello world", 0.0, 0.8, words)],
    )


def test_render_json_contains_transcript_segments_and_captions() -> None:
    transcript = sample_transcript()
    captions = [Caption("Hello world", 0.0, 0.8, list(transcript.words))]

    payload = json.loads(render_json(transcript, captions))

    assert payload["transcript"] == {
        "language": "en",
        "duration": 0.8,
        "word_count": 2,
        "segment_count": 1,
    }
    assert payload["segments"][0]["text"] == "Hello world"
    assert payload["segments"][0]["words"][0]["probability"] == 0.98
    assert payload["captions"][0]["text"] == "Hello world"
    assert payload["captions"][0]["words"][1]["text"] == "world"


def test_write_json_creates_pretty_printed_metadata_file(tmp_path: Path) -> None:
    transcript = sample_transcript()
    path = tmp_path / "sample.json"

    write_json(transcript, [Caption("Hello world", 0.0, 0.8, list(transcript.words))], path)

    output = path.read_text(encoding="utf-8")
    payload = json.loads(output)
    assert output.startswith("{\n  ")
    assert payload["transcript"]["language"] == "en"
    assert payload["segments"][0]["start"] == 0.0
    assert payload["captions"][0]["end"] == 0.8


def test_render_json_keeps_caption_only_compatibility() -> None:
    payload = json.loads(render_json([Caption("Only caption", 0.0, 1.0)]))

    assert payload["transcript"]["word_count"] == 0
    assert payload["segments"] == []
    assert payload["captions"][0]["text"] == "Only caption"
