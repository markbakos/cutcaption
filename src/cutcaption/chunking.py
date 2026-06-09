"""Convert transcript timestamps into readable caption chunks."""

from __future__ import annotations

import re

from cutcaption.config import CaptionConfig
from cutcaption.models import Caption, Segment, Transcript, Word, WordTiming

PUNCTUATION_ENDINGS = (".", "?", "!", ",", ";", ":")
LONG_PAUSE_SECONDS = 0.45
MIN_READABLE_WORDS = 2
MAX_LINE_CHARS = 26


def build_captions(transcript: Transcript, config: CaptionConfig) -> list[Caption]:
    """Build short creator-friendly captions from a transcript."""

    words = _clean_words(transcript.words)
    if words:
        chunks = _chunk_words(words, config)
        chunks = _merge_one_word_fragments(chunks, config)
        return [_caption_from_words(chunk) for chunk in chunks]

    if transcript.segments is None:
        return []
    return _captions_from_segments(transcript.segments)


def chunk_words(
    words: list[WordTiming] | tuple[WordTiming, ...],
    *,
    min_words: int = MIN_READABLE_WORDS,
    max_words: int = 5,
    max_pause: float = LONG_PAUSE_SECONDS,
) -> list[Caption]:
    """Group timestamped words into short captions.

    This compatibility wrapper keeps the original word-only API available while
    routing through the same cleanup and caption model used by build_captions.
    """

    if min_words < 1:
        raise ValueError("min_words must be at least 1.")
    if max_words < min_words:
        raise ValueError("max_words must be greater than or equal to min_words.")

    config = CaptionConfig(max_words=max_words)
    clean_words = _clean_words(words)
    chunks = _chunk_words(clean_words, config, min_words=min_words, max_pause=max_pause)
    chunks = _merge_one_word_fragments(chunks, config)
    return [_caption_from_words(chunk) for chunk in chunks]


def _chunk_words(
    words: tuple[Word, ...],
    config: CaptionConfig,
    *,
    min_words: int = MIN_READABLE_WORDS,
    max_pause: float = LONG_PAUSE_SECONDS,
) -> list[list[Word]]:
    chunks: list[list[Word]] = []
    current: list[Word] = []

    for word in words:
        if current and _should_split_before(
            current,
            word,
            config,
            min_words=min_words,
            max_pause=max_pause,
        ):
            chunks.append(current)
            current = []

        current.append(word)

    if current:
        chunks.append(current)

    return chunks


def _should_split_before(
    current: list[Word],
    next_word: Word,
    config: CaptionConfig,
    *,
    min_words: int,
    max_pause: float,
) -> bool:
    if len(current) >= config.max_words:
        return True

    if _would_exceed_max_lines(current, next_word, config):
        return _can_stand_alone(current, config, min_words=min_words)

    current_start = current[0].start
    current_end = current[-1].end
    current_duration = current_end - current_start
    would_duration = next_word.end - current_start

    if would_duration > config.max_caption_duration:
        return _can_stand_alone(current, config, min_words=1)

    previous = current[-1]
    pause = next_word.start - previous.end
    if pause > max_pause:
        return _can_stand_alone(current, config, min_words=min_words)

    if previous.text.endswith(PUNCTUATION_ENDINGS):
        return _can_stand_alone(current, config, min_words=min_words)

    return current_duration >= config.max_caption_duration


def _can_stand_alone(current: list[Word], config: CaptionConfig, *, min_words: int) -> bool:
    duration = current[-1].end - current[0].start
    if len(current) >= config.max_words:
        return True
    if duration >= config.max_caption_duration:
        return True
    return len(current) >= min_words and duration >= config.min_caption_duration


def _merge_one_word_fragments(
    chunks: list[list[Word]],
    config: CaptionConfig,
) -> list[list[Word]]:
    if len(chunks) < 2:
        return chunks

    merged: list[list[Word]] = []
    index = 0
    while index < len(chunks):
        chunk = chunks[index]
        if len(chunk) != 1:
            merged.append(chunk)
            index += 1
            continue

        if merged and _can_merge(merged[-1], chunk, config):
            merged[-1].extend(chunk)
            index += 1
            continue

        if index + 1 < len(chunks) and _can_merge(chunk, chunks[index + 1], config):
            merged.append(chunk + chunks[index + 1])
            index += 2
            continue

        merged.append(chunk)
        index += 1

    if len(merged) >= 2 and len(merged[-1]) == 1 and _can_merge(merged[-2], merged[-1], config):
        merged[-2].extend(merged.pop())
    elif (
        len(merged) >= 2
        and len(merged[-1]) == 1
        and len(merged[-2]) > MIN_READABLE_WORDS
        and _line_count(_caption_text([merged[-2][-1], *merged[-1]])) <= config.max_lines
    ):
        merged[-1].insert(0, merged[-2].pop())

    return merged


def _can_merge(left: list[Word], right: list[Word], config: CaptionConfig) -> bool:
    combined = left + right
    return (
        len(combined) <= config.max_words
        and combined[-1].end - combined[0].start <= config.max_caption_duration
        and _line_count(_caption_text(combined)) <= config.max_lines
    )


def _would_exceed_max_lines(current: list[Word], next_word: Word, config: CaptionConfig) -> bool:
    return _line_count(_caption_text([*current, next_word])) > config.max_lines


def _line_count(text: str) -> int:
    if not text:
        return 0

    lines = 1
    line_length = 0
    for token in text.split():
        token_length = len(token)
        separator = 1 if line_length else 0
        if line_length and line_length + separator + token_length > MAX_LINE_CHARS:
            lines += 1
            line_length = token_length
        else:
            line_length += separator + token_length
    return lines


def _captions_from_segments(segments: list[Segment]) -> list[Caption]:
    captions: list[Caption] = []
    for segment in segments:
        _validate_timing(segment.text, segment.start, segment.end)
        text = _clean_text(segment.text)
        if text:
            captions.append(Caption(text=text, start=segment.start, end=segment.end, words=[]))
    return captions


def _caption_from_words(words: list[Word]) -> Caption:
    return Caption(text=_caption_text(words), start=words[0].start, end=words[-1].end, words=words)


def _caption_text(words: list[Word]) -> str:
    return _clean_text(" ".join(word.text for word in words))


def _clean_words(words: list[WordTiming] | tuple[WordTiming, ...]) -> tuple[Word, ...]:
    clean_words: list[Word] = []
    for word in words:
        _validate_timing(word.text, word.start, word.end)
        text = _clean_text(word.text)
        if text:
            clean_words.append(
                Word(
                    text=text,
                    start=word.start,
                    end=word.end,
                    probability=word.probability,
                )
            )
    return tuple(clean_words)


def _clean_text(text: str) -> str:
    clean = re.sub(r"\s+", " ", text.strip())
    return re.sub(r"\s+([.,?!;:])", r"\1", clean)


def _validate_timing(text: str, start: float, end: float) -> None:
    if start < 0 or end < 0 or end <= start:
        raise ValueError(f"Invalid word timing for '{text}'.")
