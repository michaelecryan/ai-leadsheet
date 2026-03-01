from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from leadsheet import analysis, export as export_mod, midi
from leadsheet import simplify as simplify_mod

app = typer.Typer(help="Convert AI-generated MIDI or audio to a guitar lead sheet.")
console = Console()

_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}


@app.command()
def generate(
    input_path: Path = typer.Argument(..., exists=True, help="MIDI or audio file (.mid, .mp3, .wav, .flac, .ogg, .m4a)"),
    out: Path = typer.Option(..., help="Output MusicXML file path"),
    simplify: bool = typer.Option(True, "--simplify/--no-simplify", help="Apply guitar simplification rules"),
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

    capo_hint: str | None = None
    if simplify:
        simplified = simplify_mod.simplify(result)
        key_display = simplified.key
        chords_display = simplified.chords
        if simplified.capo and simplified.capo_shape_key:
            capo_hint = f"capo {simplified.capo} and play in {simplified.capo_shape_key} major shapes"
    else:
        key_display = result.key
        chords_display = result.chords

    console.print(f"\nDetected Key: [bold green]{key_display}[/bold green]")
    if capo_hint:
        console.print(f"  [yellow]Tip: {capo_hint}[/yellow]")

    progression = " | ".join(c.symbol for c in chords_display)
    console.print(f"Chord progression: {progression}")

    export_mod.export(parsed, key_display, result.gestures, chords_display, out)
    console.print(f"\nExported: [bold]{out}[/bold]")


if __name__ == "__main__":
    app()
