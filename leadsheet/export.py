"""MusicXML export — renders gestures and chord symbols into a music21 Score."""

from __future__ import annotations

from pathlib import Path

import music21

from leadsheet.analysis import Gesture, GestureKind, MeasureChord
from leadsheet.midi import ParsedMidi


# Standard quarter-length values, longest first (greedy snap)
_STANDARD_DURATIONS = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.375, 0.25, 0.125]

# Neutral pitch for slash noteheads (conventional lead sheet rhythm notation)
_SLASH_PITCH = "B4"

# A duration snaps up to the next standard value if it is within this fraction of it
_SNAP_THRESHOLD = 0.75


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
    part.insert(0, music21.clef.TrebleClef())

    tonic, mode = key.split(" ", 1)
    part.insert(0, music21.meter.TimeSignature(
        f"{parsed.time_sig_numerator}/{parsed.time_sig_denominator}"
    ))
    part.insert(0, music21.key.Key(tonic, mode))
    part.insert(0, music21.tempo.MetronomeMark(number=round(parsed.bpm)))

    # Gestures — render each type differently
    for g in gestures:
        part.insert(_snap(g.start_beat), _build_element(g))

    # Chord symbols — one per measure, placed at the downbeat
    for c in chords:
        offset = (c.measure - 1) * parsed.beats_per_measure
        try:
            cs = music21.harmony.ChordSymbol(c.symbol)
            part.insert(offset, cs)
        except Exception:
            print(f"Warning: skipping unparseable chord symbol '{c.symbol}' at measure {c.measure}")

    music21.stream.Score([part]).write("musicxml", fp=str(out))


def _build_element(g: Gesture) -> music21.base.Music21Object:
    """Return the music21 element that represents a gesture."""
    ql = _quantize(g.duration_beat)
    if g.kind == GestureKind.MELODY:
        n = music21.note.Note(g.pitches[0])
        n.quarterLength = ql
        return n
    if g.kind == GestureKind.DYAD:
        c = music21.chord.Chord(g.pitches)
        c.quarterLength = ql
        return c
    # strum — slash notehead
    n = music21.note.Note(_SLASH_PITCH)
    n.notehead = "slash"
    n.quarterLength = ql
    return n


def _snap(beat: float, grid: float = 0.125) -> float:
    """Round a beat position to the nearest 32nd-note grid."""
    return round(beat / grid) * grid


def _quantize(beats: float) -> float:
    """Snap a duration in beats to the nearest standard note value."""
    for dur in _STANDARD_DURATIONS:
        if beats >= dur * _SNAP_THRESHOLD:
            return dur
    return 0.125  # floor: 32nd note
