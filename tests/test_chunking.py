from __future__ import annotations

import pytest

from cutcaption.chunking import chunk_words
from cutcaption.models import WordTiming


def word(text: str, start: float, end: float) -> WordTiming:
    return WordTiming(text=text, start=start, end=end)


def test_chunk_words_groups_two_to_five_words() -> None:
    captions = chunk_words(
        [
            word("One", 0.0, 0.2),
            word("command", 0.2, 0.4),
            word("pretty", 0.4, 0.6),
            word("captions", 0.6, 0.8),
            word("batch", 0.8, 1.0),
            word("videos", 1.0, 1.2),
        ]
    )

    assert [caption.text for caption in captions] == ["One command pretty captions", "batch videos"]


def test_chunk_words_splits_on_punctuation_after_minimum_words() -> None:
    captions = chunk_words(
        [
            word("One", 0.0, 0.2),
            word("command.", 0.2, 0.4),
            word("Pretty", 0.5, 0.7),
            word("captions", 0.7, 0.9),
        ]
    )

    assert [caption.text for caption in captions] == ["One command.", "Pretty captions"]


def test_chunk_words_rejects_invalid_timing() -> None:
    with pytest.raises(ValueError, match="Invalid word timing"):
        chunk_words([word("bad", 1.0, 1.0)])
