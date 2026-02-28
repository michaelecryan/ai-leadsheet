from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from leadsheet import midi

app = typer.Typer(help="Convert AI-generated MIDI to a guitar lead sheet.")
console = Console()


@app.command()
def generate(
    midi_path: Path = typer.Argument(..., exists=True, help="Path to input MIDI file"),
    out: Path = typer.Option(..., help="Output MusicXML file path"),
    simplify: bool = typer.Option(True, "--simplify/--no-simplify", help="Apply guitar simplification rules"),
) -> None:
    """Convert MIDI to a clean, guitar-playable lead sheet (MusicXML)."""
    console.print(f"Loading MIDI: [bold]{midi_path}[/bold]")

    parsed = midi.load(midi_path)

    console.print(f"  Tempo:          {parsed.bpm:.1f} BPM")
    console.print(f"  Time signature: {parsed.time_sig_numerator}/{parsed.time_sig_denominator}")
    console.print(f"  Notes found:    {len(parsed.notes)}")

    # analysis, simplification, and export steps will plug in here
    console.print("\n[yellow]Pipeline not yet implemented — coming next.[/yellow]")


if __name__ == "__main__":
    app()
