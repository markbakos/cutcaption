"""Environment checks for cutcaption."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from cutcaption.utils.ffmpeg import executable_exists

FFMPEG_INSTALL_HINT = """Install ffmpeg:
  macOS: brew install ffmpeg
  Ubuntu/Debian: sudo apt install ffmpeg
  Windows: winget install Gyan.FFmpeg"""


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    ok: bool
    message: str
    critical: bool = True
    hint: str | None = None


def run_doctor_checks(cwd: Path | None = None) -> list[DoctorCheck]:
    """Run all environment checks without raising for missing dependencies."""

    working_dir = cwd or Path.cwd()
    checks = [
        check_python_version(sys.version_info[:3]),
        check_import("faster_whisper", "faster-whisper"),
        check_import("pysubs2", "pysubs2"),
        check_executable(
            "ffmpeg",
            missing_message="ffmpeg not found. Burning captions into video requires ffmpeg.",
            found_message="ffmpeg found. Burned-in video output is available.",
            hint=FFMPEG_INSTALL_HINT,
        ),
        check_executable(
            "ffprobe",
            missing_message="ffprobe not found. Media probing requires ffprobe.",
            found_message="ffprobe found. Media probing is available.",
            hint=FFMPEG_INSTALL_HINT,
        ),
        check_write_access(working_dir),
    ]
    cuda_check = check_cuda_available()
    if cuda_check is not None:
        checks.append(cuda_check)
    return checks


def has_critical_failures(checks: list[DoctorCheck]) -> bool:
    return any(check.critical and not check.ok for check in checks)


def check_python_version(version_info: tuple[int, int, int]) -> DoctorCheck:
    version = ".".join(str(part) for part in version_info)
    ok = version_info >= (3, 10, 0)
    if ok:
        return DoctorCheck("Python 3.10+", True, f"Python {version} is supported.")
    return DoctorCheck(
        "Python 3.10+",
        False,
        f"Python {version} is too old. cutcaption requires Python 3.10 or newer.",
        hint="Install Python 3.10+ and rerun cutcaption in that environment.",
    )


def check_import(module_name: str, package_name: str) -> DoctorCheck:
    if importlib.util.find_spec(module_name) is not None:
        return DoctorCheck(package_name, True, f"{package_name} available.")

    return DoctorCheck(
        package_name,
        False,
        f"{package_name} not installed.",
        hint=f"Install runtime dependencies with: python -m pip install {package_name}",
    )


def check_executable(
    name: str,
    *,
    missing_message: str,
    found_message: str,
    hint: str,
    exists: Callable[[str], bool] = executable_exists,
) -> DoctorCheck:
    if exists(name):
        return DoctorCheck(name, True, found_message)
    return DoctorCheck(name, False, missing_message, hint=hint)


def check_write_access(directory: Path) -> DoctorCheck:
    path = directory.expanduser()
    test_path = path / f".cutcaption-doctor-{uuid4().hex}.tmp"
    try:
        test_path.write_text("ok", encoding="utf-8")
        test_path.unlink()
    except OSError as exc:
        return DoctorCheck(
            "Current directory writable",
            False,
            f"Cannot write to {path}: {exc.strerror or exc}.",
            hint="Choose a writable folder or pass --output to a writable directory.",
        )
    return DoctorCheck("Current directory writable", True, f"Can write to {path}.")


def check_cuda_available() -> DoctorCheck | None:
    """Best-effort optional CUDA detection.

    CUDA is not required. If the local Python environment lacks common GPU
    packages, omit this check instead of reporting a failure.
    """

    torch_spec = importlib.util.find_spec("torch")
    if torch_spec is None:
        return None

    try:
        import torch
    except Exception:
        return DoctorCheck(
            "CUDA",
            False,
            "Could not inspect CUDA through torch. CPU transcription can still work.",
            critical=False,
        )

    if torch.cuda.is_available():
        return DoctorCheck("CUDA", True, "CUDA appears available.", critical=False)
    return DoctorCheck(
        "CUDA",
        False,
        "CUDA not detected. CPU transcription can still work.",
        critical=False,
    )
