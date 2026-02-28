from __future__ import annotations

from pathlib import Path

import music21

from leadsheet.analysis import MeasureChord
from leadsheet.midi import Note, ParsedMidi


# Standard quarter-length values, longest first (greedy snap)
_STANDARD_DURATIONS = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.375, 0.25, 0.125]


def export(
    parsed: ParsedMidi,
    key: str,
    melody: list[Note],
    chords: list[MeasureChord],
    out: Path,
) -> None:
    """Write a MusicXML lead sheet: melody + chord symbols, key sig, time sig."""
    part = music21.stream.Part()
    part.insert(0, music21.instrument.Guitar())

    tonic, mode = key.split(" ", 1)
    part.insert(0, music21.meter.TimeSignature(
        f"{parsed.time_sig_numerator}/{parsed.time_sig_denominator}"
    ))
    part.insert(0, music21.key.Key(tonic, mode))
    part.insert(0, music21.tempo.MetronomeMark(number=round(parsed.bpm)))

    # Melody — snap start positions and durations to grid so gaps are expressible
    for n in melody:
        m21n = music21.note.Note(n.pitch)
        m21n.quarterLength = _quantize(n.duration_beat)
        part.insert(_snap(n.start_beat), m21n)

    # Chord symbols — one per measure, placed at the downbeat
    for c in chords:
        offset = (c.measure - 1) * parsed.beats_per_measure
        try:
            cs = music21.harmony.ChordSymbol(c.symbol)
            part.insert(offset, cs)
        except Exception:
            pass  # skip unparseable symbols rather than crash

    music21.stream.Score([part]).write("musicxml", fp=str(out))


def _snap(beat: float, grid: float = 0.125) -> float:
    """Round a beat position to the nearest 32nd-note grid."""
    return round(beat / grid) * grid


def _quantize(beats: float) -> float:
    """Snap a duration in beats to the nearest standard note value."""
    for dur in _STANDARD_DURATIONS:
        if beats >= dur * 0.75:  # within 25% → snap up
            return dur
    return 0.125  # floor: 32nd note
