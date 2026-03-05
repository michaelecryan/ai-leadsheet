"""CLI entry point — Typer app that drives the full MIDI/audio → MusicXML pipeline."""

from __future__ import annotations

import statistics
from pathlib import Path

import music21.pitch
import typer
from rich.console import Console
from rich.table import Table

from leadsheet import analysis, export as export_mod, midi
from leadsheet import simplify as simplify_mod
from leadsheet.analysis import Gesture, GestureKind, suggest_scales

app = typer.Typer(help="Convert AI-generated MIDI or audio to a guitar lead sheet.")
console = Console()

_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}


@app.command()
def generate(
    input_path: Path = typer.Argument(..., exists=True, help="MIDI or audio file (.mid, .mp3, .wav, .flac, .ogg, .m4a)"),
    out: Path = typer.Option(..., help="Output MusicXML file path"),
    simplify: bool = typer.Option(True, "--simplify/--no-simplify", help="Apply guitar simplification rules"),
    inspect: bool = typer.Option(False, "--inspect", help="Print gesture breakdown after analysis"),
) -> None:
    """Convert a MIDI or audio file to a clean, guitar-playable lead sheet (MusicXML)."""
    if input_path.suffix.lower() in _AUDIO_EXTENSIONS:
        from leadsheet import audio as audio_mod
        console.print(f"Transcribing audio: [bold]{input_path}[/bold]")
        parsed = audio_mod.load_audio(input_path)
    else:
        console.print(f"Loading MIDI: [bold]{input_path}[/bold]")
        parsed = midi.load(input_path)

    console.print(f"  Tempo:          {parsed.bpm:.1f} BPM")
    console.print(f"  Time signature: {parsed.time_sig_numerator}/{parsed.time_sig_denominator}")
    console.print(f"  Notes found:    {len(parsed.notes)}")

    result = analysis.analyse(parsed)

    if inspect:
        _print_inspect(result.gestures, len(parsed.notes))

    capo_hint: str | None = None
    if simplify:
        simplified = simplify_mod.simplify(result)
        key_display = simplified.key
        chords_display = simplified.chords
        if simplified.capo and simplified.capo_shape_key:
            capo_hint = f"Capo {simplified.capo} and play in {simplified.capo_shape_key} shapes"
    else:
        key_display = result.key
        chords_display = result.chords

    console.print(f"\nDetected Key: [bold green]{key_display}[/bold green]")
    if capo_hint:
        console.print(f"  [yellow]Tip: {capo_hint}[/yellow]")
    scales = suggest_scales(key_display)
    if scales:
        console.print(f"  Scales: {' / '.join(scales)}")

    progression = " | ".join(c.symbol for c in chords_display)
    console.print(f"Chord progression: {progression}")

    export_mod.export(parsed, key_display, result.gestures, chords_display, out)
    txt_out = out.with_suffix(".txt")
    export_mod.export_text(chords_display, key_display, capo_hint, scales, txt_out)
    console.print(f"\nExported: [bold]{out}[/bold]")
    console.print(f"Text chart: [bold]{txt_out}[/bold]")


def _pitch_name(midi_num: int) -> str:
    """Convert a MIDI pitch number to a note name string (e.g. 64 → 'E4')."""
    return music21.pitch.Pitch(midi_num).nameWithOctave


def _print_inspect(gestures: list[Gesture], raw_note_count: int) -> None:
    """Print a gesture breakdown table and the first 10 gestures for calibration."""
    total = len(gestures)
    console.print(f"\n[bold]Gesture breakdown[/bold] ({total} gestures from {raw_note_count} raw notes)\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Kind")
    table.add_column("Count", justify="right")
    table.add_column("  %", justify="right")
    table.add_column("dur min", justify="right")
    table.add_column("dur median", justify="right")
    table.add_column("dur max", justify="right")

    for kind in GestureKind:
        subset = [g for g in gestures if g.kind == kind]
        if not subset:
            continue
        durations = [g.duration_beat for g in subset]
        pct = 100 * len(subset) / total if total else 0
        table.add_row(
            kind.value,
            str(len(subset)),
            f"{pct:.0f}%",
            f"{min(durations):.2f}",
            f"{statistics.median(durations):.2f}",
            f"{max(durations):.2f}",
        )

    console.print(table)

    console.print("\n[bold]First 10 gestures:[/bold]")
    for g in gestures[:10]:
        pitches = " ".join(_pitch_name(p) for p in g.pitches)
        symbol = f"  {g.symbol}" if g.symbol else ""
        console.print(f"  beat {g.start_beat:5.1f}  {g.kind.value:<7}  [{pitches}]{symbol}  dur={g.duration_beat:.2f}")
    console.print()


if __name__ == "__main__":
    app()
