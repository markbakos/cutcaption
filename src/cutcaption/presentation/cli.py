"""Command line interface for cutcaption."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from cutcaption import __version__
from cutcaption.application.commands import CaptionVideoCommand
from cutcaption.application.use_cases import PlanCaptionRun
from cutcaption.infrastructure.file_system import LocalFileSystem


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cutcaption",
        description="Generate styled, burned-in captions for videos.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command")
    plan_parser = subparsers.add_parser(
        "plan",
        help="Validate a video path and show the planned output directory.",
    )
    plan_parser.add_argument("source", type=Path, help="Video file to caption.")
    plan_parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Directory where generated artifacts will be written.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "plan":
        return _handle_plan(args)

    parser.print_help()
    return 0


def _handle_plan(args: argparse.Namespace) -> int:
    use_case = PlanCaptionRun(LocalFileSystem())
    plan = use_case.execute(
        CaptionVideoCommand(source=args.source, output_dir=args.output_dir),
    )
    print(f"source={plan.source}")
    print(f"output_dir={plan.output_dir}")
    return 0
