"""Transcription adapter boundary."""

from __future__ import annotations

from pathlib import Path

from cutcaption.config import CutcaptionConfig
from cutcaption.models import Transcript, WordTiming


class FasterWhisperTranscriber:
    def transcribe(self, video_path: Path, config: CutcaptionConfig) -> Transcript:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is required for transcription. "
                "Install cutcaption with its runtime dependencies."
            ) from exc

        model = WhisperModel(config.model, device="cpu", compute_type=_compute_type(config.mode))
        segments, info = model.transcribe(
            str(video_path),
            language=config.language,
            word_timestamps=True,
            vad_filter=True,
        )
        words: list[WordTiming] = []
        for segment in segments:
            for word in getattr(segment, "words", None) or []:
                text = getattr(word, "word", "").strip()
                start = getattr(word, "start", None)
                end = getattr(word, "end", None)
                if text and start is not None and end is not None:
                    words.append(WordTiming(text=text, start=float(start), end=float(end)))
        return Transcript(words=tuple(words), language=getattr(info, "language", None))


def _compute_type(mode: str) -> str:
    if mode == "accurate":
        return "float32"
    return "int8"
