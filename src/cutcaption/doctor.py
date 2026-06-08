"""Environment checks for cutcaption."""

from __future__ import annotations

from dataclasses import dataclass

from cutcaption.utils.ffmpeg import executable_exists


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    ok: bool
    message: str


def run_doctor_checks() -> list[DoctorCheck]:
    return [
        _binary_check("ffmpeg"),
        _binary_check("ffprobe"),
        _import_check("faster_whisper", "faster-whisper"),
        _import_check("pysubs2", "pysubs2"),
    ]


def _binary_check(name: str) -> DoctorCheck:
    ok = executable_exists(name)
    message = "found" if ok else f"not found. Install {name} and ensure it is on PATH."
    return DoctorCheck(name=name, ok=ok, message=message)


def _import_check(module_name: str, package_name: str) -> DoctorCheck:
    try:
        __import__(module_name)
    except ImportError:
        return DoctorCheck(
            name=package_name,
            ok=False,
            message=f"not installed. Run `python -m pip install {package_name}`.",
        )
    return DoctorCheck(name=package_name, ok=True, message="installed")
