"""Convert word-level timestamps into readable caption chunks."""

from __future__ import annotations

import re

from cutcaption.models import Caption, WordTiming

PUNCTUATION_ENDINGS = (".", "!", "?", ";", ":")


def chunk_words(
    words: list[WordTiming] | tuple[WordTiming, ...],
    *,
    min_words: int = 2,
    max_words: int = 5,
    max_pause: float = 0.65,
) -> list[Caption]:
    """Group timestamped words into short creator-friendly captions."""

    if min_words < 1:
        raise ValueError("min_words must be at least 1.")
    if max_words < min_words:
        raise ValueError("max_words must be greater than or equal to min_words.")

    chunks: list[list[WordTiming]] = []
    current: list[WordTiming] = []

    for word in words:
        if word.end <= word.start:
            raise ValueError(f"Invalid word timing for '{word.text}'.")

        if current and _should_split(
            current,
            word,
            min_words=min_words,
            max_words=max_words,
            max_pause=max_pause,
        ):
            chunks.append(current)
            current = []

        current.append(word)

    if current:
        chunks.append(current)

    return [
        _caption_from_words(chunk)
        for chunk in _merge_weak_fragments(chunks, max_words=max_words)
    ]


def _should_split(
    current: list[WordTiming],
    next_word: WordTiming,
    *,
    min_words: int,
    max_words: int,
    max_pause: float,
) -> bool:
    if len(current) >= max_words:
        return True
    if len(current) < min_words:
        return False
    previous = current[-1]
    if next_word.start - previous.end >= max_pause:
        return True
    return previous.text.endswith(PUNCTUATION_ENDINGS)


def _merge_weak_fragments(
    chunks: list[list[WordTiming]],
    *,
    max_words: int,
) -> list[list[WordTiming]]:
    if len(chunks) < 2:
        return chunks

    merged: list[list[WordTiming]] = []
    for chunk in chunks:
        if len(chunk) == 1 and merged and len(merged[-1]) < max_words:
            merged[-1].extend(chunk)
        else:
            merged.append(chunk)

    if len(merged) >= 2 and len(merged[-1]) == 1 and len(merged[-2]) < max_words:
        merged[-2].extend(merged.pop())
    elif len(merged) >= 2 and len(merged[-1]) == 1 and len(merged[-2]) > 2:
        merged[-1].insert(0, merged[-2].pop())

    return merged


def _caption_from_words(words: list[WordTiming]) -> Caption:
    text = " ".join(_clean_word(word.text) for word in words).strip()
    return Caption(text=text, start=words[0].start, end=words[-1].end)


def _clean_word(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())
