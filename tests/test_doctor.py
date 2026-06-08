from __future__ import annotations

from pathlib import Path

from cutcaption.doctor import (
    FFMPEG_INSTALL_HINT,
    DoctorCheck,
    check_executable,
    check_python_version,
    check_write_access,
    has_critical_failures,
)


def test_check_python_version_accepts_supported_version() -> None:
    check = check_python_version((3, 10, 0))

    assert check.ok is True
    assert check.critical is True
    assert "supported" in check.message


def test_check_python_version_rejects_old_version_with_hint() -> None:
    check = check_python_version((3, 9, 18))

    assert check.ok is False
    assert check.critical is True
    assert "requires Python 3.10" in check.message
    assert check.hint is not None


def test_check_executable_reports_missing_ffmpeg_with_install_hint() -> None:
    check = check_executable(
        "ffmpeg",
        missing_message="ffmpeg not found. Burning captions into video requires ffmpeg.",
        found_message="ffmpeg found.",
        hint=FFMPEG_INSTALL_HINT,
        exists=lambda _: False,
    )

    assert check.ok is False
    assert "Burning captions into video requires ffmpeg" in check.message
    assert "brew install ffmpeg" in str(check.hint)
    assert "sudo apt install ffmpeg" in str(check.hint)
    assert "winget install Gyan.FFmpeg" in str(check.hint)


def test_check_executable_reports_available_tool() -> None:
    check = check_executable(
        "ffmpeg",
        missing_message="missing",
        found_message="ffmpeg found.",
        hint=FFMPEG_INSTALL_HINT,
        exists=lambda _: True,
    )

    assert check.ok is True
    assert check.message == "ffmpeg found."
    assert check.hint is None


def test_check_write_access_accepts_writable_directory(tmp_path: Path) -> None:
    check = check_write_access(tmp_path)

    assert check.ok is True
    assert not list(tmp_path.glob(".cutcaption-doctor-*.tmp"))


def test_has_critical_failures_ignores_optional_failures() -> None:
    checks = [
        DoctorCheck("critical", True, "ok", critical=True),
        DoctorCheck("optional", False, "missing", critical=False),
    ]

    assert has_critical_failures(checks) is False


def test_has_critical_failures_detects_critical_failure() -> None:
    checks = [DoctorCheck("critical", False, "missing", critical=True)]

    assert has_critical_failures(checks) is True
