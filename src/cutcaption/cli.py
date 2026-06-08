"""Typer-based command line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from cutcaption import __version__
from cutcaption.config import CutcaptionConfig
from cutcaption.doctor import run_doctor_checks
from cutcaption.pipeline import CaptionPipeline
from cutcaption.styles import STYLES

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
    preset: Annotated[str, typer.Option("--preset", help="Caption preset.")] = "shorts",
    style: Annotated[str, typer.Option("--style", help="Caption style preset.")] = "clean",
    model: Annotated[str, typer.Option("--model", help="faster-whisper model name.")] = "small",
    mode: Annotated[
        str,
        typer.Option("--mode", help="Processing mode: fast, balanced, accurate."),
    ] = "balanced",
    language: Annotated[
        str | None,
        typer.Option("--language", help="Language code, or omit for auto detection."),
    ] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output directory.")] = None,
    srt: Annotated[bool, typer.Option("--srt/--no-srt", help="Write SRT subtitles.")] = True,
    ass: Annotated[
        bool,
        typer.Option("--ass/--no-ass", help="Write ASS subtitles."),
    ] = False,
    burn: Annotated[
        bool,
        typer.Option("--burn/--no-burn", help="Render burned-in captioned MP4."),
    ] = True,
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
        config = CutcaptionConfig(
            preset=preset,
            style=style,
            model=model,
            mode=mode,
            language=language,
            output=output,
            write_srt=srt,
            write_ass=ass,
            burn=burn,
        )
        results = CaptionPipeline().run(input_path, config)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    for result in results:
        console.print(f"[green]Done[/green] {result.job.source.name}")


@app.command()
def doctor() -> None:
    """Check local tools and Python dependencies."""

    table = Table(title="cutcaption doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    failed = False
    for check in run_doctor_checks():
        failed = failed or not check.ok
        table.add_row(
            check.name,
            "[green]ok[/green]" if check.ok else "[red]missing[/red]",
            check.message,
        )
    console.print(table)
    if failed:
        raise typer.Exit(code=1)


@app.command("styles")
def list_styles() -> None:
    """List built-in caption styles."""

    table = Table(title="Caption styles")
    table.add_column("Name")
    table.add_column("Font")
    table.add_column("Size")
    for style in STYLES.values():
        table.add_row(style.name, style.font_name, str(style.font_size))
    console.print(table)


@app.command()
def init() -> None:
    """Create a starter config file."""

    config_path = Path("cutcaption.toml")
    if config_path.exists():
        console.print("[yellow]cutcaption.toml already exists.[/yellow]")
        raise typer.Exit(code=1)
    config_path.write_text(
        'preset = "shorts"\nstyle = "clean"\nmodel = "small"\nmode = "balanced"\n',
        encoding="utf-8",
    )
    console.print("[green]Created cutcaption.toml[/green]")


@app.command()
def preview() -> None:
    """Preview caption styles. Stubbed for the MVP foundation."""

    console.print("[yellow]Preview is not implemented yet.[/yellow]")


def main() -> None:
    app()
