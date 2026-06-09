from __future__ import annotations

import pytest

from cutcaption.chunking import build_captions, chunk_words
from cutcaption.config import CaptionConfig
from cutcaption.models import Segment, Transcript, Word, WordTiming


def word(text: str, start: float, end: float) -> WordTiming:
    return WordTiming(text=text, start=start, end=end)


def transcript(words: list[Word]) -> Transcript:
    return Transcript(segments=[Segment(text="", start=0.0, end=words[-1].end, words=words)])


def test_build_captions_returns_empty_list_for_empty_transcript() -> None:
    assert build_captions(Transcript(), CaptionConfig()) == []


def test_build_captions_groups_short_readable_chunks() -> None:
    captions = build_captions(
        transcript(
            [
                word("One", 0.0, 0.2),
                word("command", 0.2, 0.4),
                word("pretty", 0.4, 0.6),
                word("captions", 0.6, 0.8),
                word("batch", 0.8, 1.0),
                word("videos", 1.0, 1.2),
            ]
        ),
        CaptionConfig(max_words=5),
    )

    assert [caption.text for caption in captions] == ["One command pretty captions", "batch videos"]
    assert all(1 <= len(caption.words) <= 5 for caption in captions)
    assert all(caption.start < caption.end for caption in captions)


def test_build_captions_splits_on_punctuation() -> None:
    captions = build_captions(
        transcript(
            [
                word("One", 0.0, 0.2),
                word("command.", 0.2, 0.4),
                word("Pretty", 0.5, 0.7),
                word("captions", 0.7, 0.9),
            ]
        ),
        CaptionConfig(),
    )

    assert [caption.text for caption in captions] == ["One command.", "Pretty captions"]


def test_build_captions_splits_on_long_pause() -> None:
    captions = build_captions(
        transcript(
            [
                word("Keep", 0.0, 0.2),
                word("moving", 0.2, 0.4),
                word("Then", 0.95, 1.15),
                word("reset", 1.15, 1.35),
            ]
        ),
        CaptionConfig(),
    )

    assert [caption.text for caption in captions] == ["Keep moving", "Then reset"]


def test_build_captions_uses_segment_fallback_without_word_timestamps() -> None:
    captions = build_captions(
        Transcript(
            segments=[
                Segment(text="  First   segment . ", start=0.0, end=1.0, words=[]),
                Segment(text="Second segment", start=1.1, end=2.0, words=[]),
            ]
        ),
        CaptionConfig(),
    )

    assert [caption.text for caption in captions] == ["First segment.", "Second segment"]
    assert [caption.words for caption in captions] == [[], []]
    assert [(caption.start, caption.end) for caption in captions] == [(0.0, 1.0), (1.1, 2.0)]


def test_build_captions_merges_one_word_fragment_when_possible() -> None:
    captions = build_captions(
        transcript(
            [
                word("Go!", 0.0, 0.2),
                word("Build", 0.25, 0.45),
                word("better", 0.45, 0.65),
                word("captions", 0.65, 0.85),
            ]
        ),
        CaptionConfig(max_words=4),
    )

    assert [caption.text for caption in captions] == ["Go! Build better captions"]
    assert len(captions[0].words) == 4


def test_build_captions_splits_to_avoid_max_duration() -> None:
    captions = build_captions(
        transcript(
            [
                word("This", 0.0, 0.4),
                word("caption", 0.4, 0.8),
                word("must", 0.8, 1.2),
                word("split", 1.2, 1.6),
                word("now", 1.6, 2.0),
            ]
        ),
        CaptionConfig(max_words=5, max_caption_duration=1.05),
    )

    assert [caption.text for caption in captions] == ["This caption", "must split", "now"]
    assert all(caption.end - caption.start <= 1.05 for caption in captions)
    assert all(caption.start < caption.end for caption in captions)


def test_build_captions_cleans_text_spacing_without_uppercasing() -> None:
    captions = build_captions(
        transcript(
            [
                word("  hello ", 0.0, 0.2),
                word(" , ", 0.2, 0.3),
                word("   world ", 0.3, 0.5),
                word(" ! ", 0.5, 0.6),
            ]
        ),
        CaptionConfig(max_words=4),
    )

    assert [caption.text for caption in captions] == ["hello,", "world!"]


def test_chunk_words_keeps_compatibility_wrapper() -> None:
    captions = chunk_words([word("Tiny", 0.0, 0.2), word("wrapper", 0.2, 0.4)])

    assert [caption.text for caption in captions] == ["Tiny wrapper"]
    assert captions[0].words == [word("Tiny", 0.0, 0.2), word("wrapper", 0.2, 0.4)]


def test_chunk_words_rejects_invalid_timing() -> None:
    with pytest.raises(ValueError, match="Invalid word timing"):
        chunk_words([word("bad", 1.0, 1.0)])
