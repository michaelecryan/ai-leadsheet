from __future__ import annotations

from pathlib import Path

import music21

from leadsheet.analysis import Gesture, MeasureChord
from leadsheet.midi import ParsedMidi


# Standard quarter-length values, longest first (greedy snap)
_STANDARD_DURATIONS = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.375, 0.25, 0.125]

# Neutral pitch for slash noteheads (conventional lead sheet rhythm notation)
_SLASH_PITCH = "B4"


def export(
    parsed: ParsedMidi,
    key: str,
    gestures: list[Gesture],
    chords: list[MeasureChord],
    out: Path,
) -> None:
    """Write a MusicXML lead sheet: gesture notation + chord symbols, key sig, time sig."""
    part = music21.stream.Part()
    part.insert(0, music21.instrument.Guitar())

    tonic, mode = key.split(" ", 1)
    part.insert(0, music21.meter.TimeSignature(
        f"{parsed.time_sig_numerator}/{parsed.time_sig_denominator}"
    ))
    part.insert(0, music21.key.Key(tonic, mode))
    part.insert(0, music21.tempo.MetronomeMark(number=round(parsed.bpm)))

    # Gestures — render each type differently
    for g in gestures:
        ql = _quantize(g.duration_beat)
        offset = _snap(g.start_beat)

        if g.kind == "melody":
            m21n = music21.note.Note(g.pitches[0])
            m21n.quarterLength = ql
            part.insert(offset, m21n)

        elif g.kind == "dyad":
            m21c = music21.chord.Chord(g.pitches)
            m21c.quarterLength = ql
            part.insert(offset, m21c)

        elif g.kind == "strum":
            m21n = music21.note.Note(_SLASH_PITCH)
            m21n.notehead = "slash"
            m21n.quarterLength = ql
            part.insert(offset, m21n)

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
