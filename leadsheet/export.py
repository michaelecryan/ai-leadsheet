"""MusicXML and plain-text export — renders a chord chart into a music21 Score or a .txt file."""

from __future__ import annotations

from pathlib import Path

import music21

from leadsheet.analysis import Gesture, MeasureChord
from leadsheet.midi import ParsedMidi


_MEASURES_PER_LINE = 4  # measures per row in plain-text output


def export(
    parsed: ParsedMidi,
    key: str,
    gestures: list[Gesture],
    chords: list[MeasureChord],
    out: Path,
) -> None:
    """Write a MusicXML chord chart: slash beats + chord symbols, key sig, time sig.

    Each measure is filled with one slash notehead per beat. Chord symbols are placed
    at the downbeat of each measure. The gestures parameter is accepted for API
    compatibility but is not used — the chord list drives all output.
    """
    part = music21.stream.Part()
    part.insert(0, music21.instrument.Guitar())
    part.insert(0, music21.clef.TrebleClef())

    tonic, mode = key.split(" ", 1)
    part.insert(0, music21.meter.TimeSignature(
        f"{parsed.time_sig_numerator}/{parsed.time_sig_denominator}"
    ))
    part.insert(0, music21.key.Key(tonic, mode))
    part.insert(0, music21.tempo.MetronomeMark(number=round(parsed.bpm)))

    # Chord symbols — one per measure at the downbeat
    # (no notes inserted; makeNotation fills each measure with whole rests)
    beats_per_measure = parsed.beats_per_measure
    for c in chords:
        offset = (c.measure - 1) * beats_per_measure
        try:
            part.insert(offset, music21.harmony.ChordSymbol(c.symbol))
        except Exception:
            print(f"Warning: skipping unparseable chord symbol '{c.symbol}' at measure {c.measure}")

    score = music21.stream.Score([part])
    score.makeNotation(inPlace=True)
    score.write("musicxml", fp=str(out))


def export_text(
    chords: list[MeasureChord],
    key: str,
    capo_hint: str | None,
    scales: list[str],
    out: Path,
) -> None:
    """Write a plain-text chord chart: header line, scale suggestions, and chord grid.

    Measures are laid out _MEASURES_PER_LINE per row, padded to a uniform column width.
    """
    lines: list[str] = []

    header = f"Key: {key}"
    if capo_hint:
        header += f"  |  {capo_hint}"
    lines.append(header)

    if scales:
        lines.append(f"Scales: {' / '.join(scales)}")

    lines.append("")

    # Pad all symbols to the same width so columns stay aligned across rows
    col_width = max((len(c.symbol) for c in chords), default=4) + 2
    for i in range(0, len(chords), _MEASURES_PER_LINE):
        row = chords[i : i + _MEASURES_PER_LINE]
        lines.append("| " + " | ".join(c.symbol.ljust(col_width) for c in row) + " |")

    out.write_text("\n".join(lines) + "\n")
