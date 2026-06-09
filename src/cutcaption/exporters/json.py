"""JSON metadata exporter."""

from __future__ import annotations

import json
from pathlib import Path

from cutcaption.models import Caption, Segment, Transcript, Word


def render_json(
    transcript: Transcript | list[Caption] | tuple[Caption, ...],
    captions: list[Caption] | tuple[Caption, ...] | None = None,
) -> str:
    if captions is None:
        captions = transcript  # Backward-compatible caption-only rendering.
        transcript = Transcript()

    payload = {
        "transcript": _transcript_metadata(transcript),
        "segments": [_segment_payload(segment) for segment in transcript.segments or []],
        "captions": [_caption_payload(caption) for caption in captions],
    }
    return json.dumps(payload, indent=2) + "\n"


def write_json(transcript: Transcript, captions: list[Caption], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(transcript, captions), encoding="utf-8")


def _transcript_metadata(transcript: Transcript) -> dict[str, object]:
    return {
        "language": transcript.language,
        "duration": transcript.duration,
        "word_count": len(transcript.words),
        "segment_count": len(transcript.segments or []),
    }


def _segment_payload(segment: Segment) -> dict[str, object]:
    return {
        "text": segment.text,
        "start": segment.start,
        "end": segment.end,
        "words": [_word_payload(word) for word in segment.words],
    }


def _caption_payload(caption: Caption) -> dict[str, object]:
    return {
        "text": caption.text,
        "start": caption.start,
        "end": caption.end,
        "words": [_word_payload(word) for word in caption.words],
    }


def _word_payload(word: Word) -> dict[str, object]:
    payload: dict[str, object] = {
        "text": word.text,
        "start": word.start,
        "end": word.end,
    }
    if word.probability is not None:
        payload["probability"] = word.probability
    return payload
