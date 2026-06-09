"""Typer-based command line interface."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cutcaption import __version__
from cutcaption.config import CutcapConfig, load_config, write_default_config
from cutcaption.doctor import DoctorCheck, has_critical_failures, run_doctor_checks
from cutcaption.models import BatchResult, JobResult, VideoJob
from cutcaption.pipeline import plan_jobs, process_batch
from cutcaption.styles import list_styles as available_styles
from cutcaption.utils.paths import folder_output_dir

app = typer.Typer(
    add_completion=False,
    help="One command. Pretty captions. Batch videos. No editing software.",
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"cutcaption {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def caption(
    ctx: typer.Context,
    input_path: Annotated[
        Path | None,
        typer.Argument(help="Video file or folder to caption."),
    ] = None,
    config_path: Annotated[
        Path | None,
        typer.Option("--config", help="Path to a cutcaption TOML config file."),
    ] = None,
    preset: Annotated[str | None, typer.Option("--preset", help="Caption preset.")] = None,
    style: Annotated[str | None, typer.Option("--style", help="Caption style preset.")] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="faster-whisper model name."),
    ] = None,
    mode: Annotated[
        str | None,
        typer.Option("--mode", help="Processing mode: fast, balanced, accurate."),
    ] = None,
    language: Annotated[
        str | None,
        typer.Option("--language", help="Language code, or omit for auto detection."),
    ] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output directory.")] = None,
    srt: Annotated[bool | None, typer.Option("--srt/--no-srt", help="Write SRT subtitles.")] = None,
    ass: Annotated[
        bool | None,
        typer.Option("--ass/--no-ass", help="Write ASS subtitles."),
    ] = None,
    json_output: Annotated[
        bool | None,
        typer.Option("--json/--no-json", help="Write JSON metadata."),
    ] = None,
    burn: Annotated[
        bool | None,
        typer.Option("--burn/--no-burn", help="Render burned-in captioned MP4."),
    ] = None,
    recursive: Annotated[
        bool | None,
        typer.Option("--recursive/--no-recursive", help="Search folders recursively."),
    ] = None,
    overwrite: Annotated[
        bool | None,
        typer.Option("--overwrite/--no-overwrite", help="Replace existing outputs."),
    ] = None,
    skip_existing: Annotated[
        bool | None,
        typer.Option(
            "--skip-existing/--no-skip-existing",
            help="Skip jobs with existing requested outputs.",
        ),
    ] = None,
    jobs: Annotated[
        int | None,
        typer.Option("--jobs", help="Number of worker jobs. Currently processed sequentially."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Plan jobs without transcription or rendering."),
    ] = False,
    version: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = False,
) -> None:
    _ = version
    if ctx.invoked_subcommand is not None:
        return
    if input_path is None:
        console.print(ctx.get_help())
        raise typer.Exit()

    try:
        config = _apply_cli_overrides(
            load_config(config_path),
            preset=preset,
            style=style,
            model=model,
            mode=mode,
            language=language,
            output=output,
            srt=srt,
            ass=ass,
            json_output=json_output,
            burn=burn,
            recursive=recursive,
            overwrite=overwrite,
            skip_existing=skip_existing,
            jobs=jobs,
        )
        planned_jobs = plan_jobs(input_path, config)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    _print_planned_jobs(planned_jobs)
    if dry_run:
        console.print("[yellow]Dry run complete. No files were processed.[/yellow]")
        return

    with console.status("[bold cyan]Processing videos...[/bold cyan]"):
        result = process_batch(
            [job.source for job in planned_jobs],
            config,
            folder_output_dir(input_path, config.output),
        )

    _print_batch_summary(result)
    if result.failed:
        raise typer.Exit(code=1)


@app.command()
def doctor() -> None:
    """Check local tools and Python dependencies."""

    checks = run_doctor_checks()
    table = Table(title="cutcaption doctor", show_lines=True)
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    for check in checks:
        table.add_row(
            check.name,
            _doctor_status(check),
            check.message,
        )

    console.print(
        Panel(
            "ffmpeg is required for burned-in captioned videos. "
            "Transcription and subtitle export may still work without it.",
            title="Video rendering",
            border_style="cyan",
        )
    )
    console.print(table)

    hints = _doctor_hints(checks)
    if hints:
        console.print(Panel("\n\n".join(hints), title="Actionable fixes", border_style="yellow"))

    if has_critical_failures(checks):
        raise typer.Exit(code=1)


@app.command("styles")
def list_styles() -> None:
    """List built-in caption styles."""

    table = Table(title="Caption styles")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Uppercase")
    table.add_column("Font size")
    table.add_column("Box")
    for style in available_styles():
        table.add_row(
            style.name,
            style.description,
            "yes" if style.uppercase else "no",
            str(style.font_size),
            "yes" if style.box else "no",
        )
    console.print(table)


@app.command()
def init() -> None:
    """Create a starter config file."""

    config_path = Path("cutcaption.toml")
    if config_path.exists():
        console.print("[yellow]cutcaption.toml already exists.[/yellow]")
        raise typer.Exit(code=1)
    write_default_config(config_path)
    console.print("[green]Created cutcaption.toml[/green]")


@app.command()
def preview() -> None:
    """Preview caption styles. Stubbed for the MVP foundation."""

    console.print("[yellow]Preview is not implemented yet.[/yellow]")


def main() -> None:
    app()


def _apply_cli_overrides(
    config: CutcapConfig,
    *,
    preset: str | None,
    style: str | None,
    model: str | None,
    mode: str | None,
    language: str | None,
    output: Path | None,
    srt: bool | None,
    ass: bool | None,
    json_output: bool | None,
    burn: bool | None,
    recursive: bool | None,
    overwrite: bool | None,
    skip_existing: bool | None,
    jobs: int | None,
) -> CutcapConfig:
    transcription = replace(
        config.transcription,
        **_without_none({"model": model, "mode": mode, "language": language}),
    )
    caption = replace(config.caption, **_without_none({"preset": preset, "style": style}))
    render = replace(
        config.render,
        **_without_none({"srt": srt, "ass": ass, "json": json_output, "burn": burn}),
    )
    batch_overrides = _without_none(
        {
            "recursive": recursive,
            "overwrite": overwrite,
            "skip_existing": skip_existing,
            "jobs": jobs,
        }
    )
    if overwrite is True and skip_existing is None:
        batch_overrides["skip_existing"] = False
    batch = replace(config.batch, **batch_overrides)
    return CutcapConfig(
        transcription=transcription,
        caption=caption,
        render=render,
        batch=batch,
        output=output if output is not None else config.output,
    )


def _without_none(values: dict[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _doctor_status(check: DoctorCheck) -> str:
    if check.ok:
        return "[green]✓ ok[/green]"
    if check.critical:
        return "[red]✗ missing[/red]"
    return "[yellow]optional[/yellow]"


def _doctor_hints(checks: list[DoctorCheck]) -> list[str]:
    hints: list[str] = []
    for check in checks:
        if not check.ok and check.hint and check.hint not in hints:
            hints.append(check.hint)
    return hints


def _print_planned_jobs(jobs: list[VideoJob]) -> None:
    table = Table(title=f"Planned caption jobs ({len(jobs)})")
    table.add_column("Input")
    table.add_column("SRT")
    table.add_column("ASS")
    table.add_column("JSON")
    table.add_column("Captioned video")

    for job in jobs:
        table.add_row(
            str(job.source),
            str(job.srt_path),
            str(job.ass_path),
            str(job.json_path),
            str(job.rendered_path),
        )

    console.print(table)


def _print_batch_summary(result: BatchResult) -> None:
    table = Table(title="Caption results")
    table.add_column("Input")
    table.add_column("Status")
    table.add_column("Outputs")
    table.add_column("Duration")
    table.add_column("Error")

    for job_result in result.results:
        table.add_row(
            str(job_result.input_path),
            _result_status(job_result),
            "\n".join(str(path) for path in job_result.outputs_written) or "-",
            f"{job_result.duration:.2f}s" if job_result.duration is not None else "-",
            job_result.error_message or "-",
        )

    console.print(table)
    console.print(
        f"Total: {result.total}  "
        f"Succeeded: {result.succeeded}  "
        f"Failed: {result.failed}  "
        f"Skipped: {result.skipped}"
    )


def _result_status(result: JobResult) -> str:
    if result.skipped:
        return "[yellow]skipped[/yellow]"
    if result.success:
        return "[green]success[/green]"
    return "[red]failed[/red]"
