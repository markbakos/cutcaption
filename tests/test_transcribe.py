from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from cutcaption.config import TranscriptionConfig
from cutcaption.transcribe import transcribe_video


def test_transcribe_video_passes_expected_faster_whisper_options(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    class FakeWhisperModel:
        def __init__(self, model: str, *, device: str, compute_type: str) -> None:
            captured["model"] = model
            captured["device"] = device
            captured["compute_type"] = compute_type

        def transcribe(self, path: str, **kwargs: object) -> object:
            captured["path"] = path
            captured["kwargs"] = kwargs
            return (
                [
                    SimpleNamespace(
                        text=" hello world",
                        start=0.0,
                        end=1.0,
                        words=[
                            SimpleNamespace(
                                word=" hello",
                                start=0.0,
                                end=0.4,
                                probability=0.9,
                            ),
                            SimpleNamespace(
                                word="world",
                                start=0.4,
                                end=1.0,
                                probability=0.8,
                            ),
                        ],
                    )
                ],
                SimpleNamespace(language="en", duration=1.23),
            )

    _install_fake_faster_whisper(monkeypatch, FakeWhisperModel)
    video = tmp_path / "video.mp4"

    transcript = transcribe_video(
        video,
        TranscriptionConfig(
            model="small",
            mode="balanced",
            language="en",
            device="auto",
            compute_type="auto",
        ),
    )

    assert captured["model"] == "small"
    assert captured["device"] == "cpu"
    assert captured["compute_type"] == "int8"
    assert captured["path"] == str(video)
    assert captured["kwargs"] == {
        "language": "en",
        "word_timestamps": True,
        "beam_size": 3,
        "vad_filter": True,
    }
    assert transcript.language == "en"
    assert transcript.duration == 1.23
    assert len(transcript.segments or []) == 1
    assert [word.text for word in transcript.words] == ["hello", "world"]
    assert transcript.words[0].probability == 0.9


@pytest.mark.parametrize(
    ("mode", "beam_size"),
    [
        ("fast", 1),
        ("balanced", 3),
        ("accurate", 5),
    ],
)
def test_transcribe_video_uses_mode_beam_size(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode: str,
    beam_size: int,
) -> None:
    captured: dict[str, object] = {}

    class FakeWhisperModel:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def transcribe(self, _path: str, **kwargs: object) -> object:
            captured["beam_size"] = kwargs["beam_size"]
            return ([], SimpleNamespace(language=None, duration=None))

    _install_fake_faster_whisper(monkeypatch, FakeWhisperModel)

    transcribe_video(
        tmp_path / "video.mp4",
        TranscriptionConfig(mode=mode),  # type: ignore[arg-type]
    )

    assert captured["beam_size"] == beam_size


def test_transcribe_video_uses_cuda_float16_when_auto_compute(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    class FakeWhisperModel:
        def __init__(self, _model: str, *, device: str, compute_type: str) -> None:
            captured["device"] = device
            captured["compute_type"] = compute_type

        def transcribe(self, _path: str, **_kwargs: object) -> object:
            return ([], SimpleNamespace(language=None, duration=None))

    _install_fake_faster_whisper(monkeypatch, FakeWhisperModel)

    transcribe_video(tmp_path / "video.mp4", TranscriptionConfig(device="cuda"))

    assert captured["device"] == "cuda"
    assert captured["compute_type"] == "float16"


def test_transcribe_video_falls_back_to_int8_when_auto_compute_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    attempts: list[tuple[str, str]] = []

    class FakeWhisperModel:
        def __init__(self, _model: str, *, device: str, compute_type: str) -> None:
            attempts.append((device, compute_type))
            if compute_type == "float16":
                raise RuntimeError("float16 unsupported")

        def transcribe(self, _path: str, **_kwargs: object) -> object:
            return ([], SimpleNamespace(language=None, duration=None))

    _install_fake_faster_whisper(monkeypatch, FakeWhisperModel)

    transcribe_video(tmp_path / "video.mp4", TranscriptionConfig(device="cuda"))

    assert attempts == [("cuda", "float16"), ("cuda", "int8")]


def test_transcribe_video_model_load_failure_has_friendly_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeWhisperModel:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise RuntimeError("model unavailable")

    _install_fake_faster_whisper(monkeypatch, FakeWhisperModel)

    with pytest.raises(RuntimeError, match="Could not load faster-whisper model 'small'"):
        transcribe_video(tmp_path / "video.mp4", TranscriptionConfig())


def test_transcribe_video_missing_dependency_has_friendly_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setitem(sys.modules, "faster_whisper", None)

    with pytest.raises(RuntimeError, match="faster-whisper is required for transcription"):
        transcribe_video(tmp_path / "video.mp4", TranscriptionConfig())


def _install_fake_faster_whisper(
    monkeypatch: pytest.MonkeyPatch,
    whisper_model: type[object],
) -> None:
    module = ModuleType("faster_whisper")
    module.WhisperModel = whisper_model  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "faster_whisper", module)
