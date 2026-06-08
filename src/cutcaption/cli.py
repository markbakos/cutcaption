"""Typer-based command line interface."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from cutcaption import __version__
from cutcaption.config import CutcapConfig, load_config, write_default_config
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
    burn: Annotated[
        bool | None,
        typer.Option("--burn/--no-burn", help="Render burned-in captioned MP4."),
    ] = None,
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
    burn: bool | None,
) -> CutcapConfig:
    transcription = replace(
        config.transcription,
        **_without_none({"model": model, "mode": mode, "language": language}),
    )
    caption = replace(config.caption, **_without_none({"preset": preset, "style": style}))
    render = replace(config.render, **_without_none({"srt": srt, "ass": ass, "burn": burn}))
    return CutcapConfig(
        transcription=transcription,
        caption=caption,
        render=render,
        batch=config.batch,
        output=output if output is not None else config.output,
    )


def _without_none(values: dict[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}
