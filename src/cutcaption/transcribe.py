"""faster-whisper transcription adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cutcaption.config import CutcapConfig, TranscriptionConfig
from cutcaption.models import Segment, Transcript, Word


def transcribe_video(path: Path, config: TranscriptionConfig) -> Transcript:
    """Transcribe a video with faster-whisper and capture word timestamps."""

    model = _load_model(config)
    try:
        segments, info = model.transcribe(
            str(path),
            language=config.language,
            word_timestamps=True,
            beam_size=_beam_size(config.mode),
            vad_filter=True,
        )
    except Exception as exc:
        raise RuntimeError(f"Transcription failed for '{path}': {exc}") from exc

    return _build_transcript(segments, info)


class FasterWhisperTranscriber:
    def transcribe(
        self,
        video_path: Path,
        config: CutcapConfig | TranscriptionConfig,
    ) -> Transcript:
        transcription_config = (
            config.transcription if isinstance(config, CutcapConfig) else config
        )
        return transcribe_video(video_path, transcription_config)


def _load_model(config: TranscriptionConfig) -> Any:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is required for transcription. "
            "Install cutcaption with its runtime dependencies."
        ) from exc

    device = _resolve_device(config.device)
    compute_type = _resolve_compute_type(device, config.compute_type)

    try:
        return WhisperModel(config.model, device=device, compute_type=compute_type)
    except Exception as exc:
        if config.compute_type == "auto" and compute_type != "int8":
            try:
                return WhisperModel(config.model, device=device, compute_type="int8")
            except Exception as fallback_exc:
                raise _model_load_error(config.model, fallback_exc) from fallback_exc
        raise _model_load_error(config.model, exc) from exc


def _model_load_error(model: str, exc: Exception) -> RuntimeError:
    return RuntimeError(
        f"Could not load faster-whisper model '{model}': {exc}. "
        "Try a smaller model, check available disk space, or run `cutcaption doctor`."
    )


def _build_transcript(segments: Any, info: Any) -> Transcript:
    transcript_segments: list[Segment] = []
    for segment in segments:
        words = [_word_from_faster_whisper(word) for word in getattr(segment, "words", None) or []]
        transcript_segments.append(
            Segment(
                text=str(getattr(segment, "text", "")).strip(),
                start=float(getattr(segment, "start", 0.0)),
                end=float(getattr(segment, "end", 0.0)),
                words=[word for word in words if word is not None],
            )
        )

    return Transcript(
        language=getattr(info, "language", None),
        duration=_optional_float(getattr(info, "duration", None)),
        segments=transcript_segments,
    )


def _word_from_faster_whisper(word: Any) -> Word | None:
    text = str(getattr(word, "word", "")).strip()
    start = getattr(word, "start", None)
    end = getattr(word, "end", None)
    if not text or start is None or end is None:
        return None
    return Word(
        text=text,
        start=float(start),
        end=float(end),
        probability=_optional_float(getattr(word, "probability", None)),
    )


def _beam_size(mode: str) -> int:
    if mode == "fast":
        return 1
    if mode == "accurate":
        return 5
    return 3


def _resolve_device(device: str) -> str:
    if device == "auto":
        return "cpu"
    return device


def _resolve_compute_type(device: str, compute_type: str) -> str:
    if compute_type != "auto":
        return compute_type
    if device == "cuda":
        return "float16"
    return "int8"


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
