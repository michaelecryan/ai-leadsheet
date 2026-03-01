"""Analysis — key detection, gesture classification, and chord grouping from a ParsedMidi."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from enum import Enum
from functools import lru_cache

import music21

from leadsheet.midi import Note, ParsedMidi


class GestureKind(str, Enum):
    MELODY = "melody"
    DYAD = "dyad"
    STRUM = "strum"


@dataclass
class MeasureChord:
    measure: int    # 1-indexed
    symbol: str     # e.g. "Em", "Cmaj7", "G"


@dataclass
class Gesture:
    kind: GestureKind
    start_beat: float
    duration_beat: float
    pitches: list[int]      # sorted low→high; 1 pitch for melody
    symbol: str | None      # chord symbol for strum; None for melody/dyad


@dataclass
class Analysis:
    key: str                      # e.g. "E major"
    gestures: list[Gesture]       # classified note events
    chords: list[MeasureChord]    # one chord symbol per measure


def analyse(parsed: ParsedMidi) -> Analysis:
    """Run full analysis on a parsed MIDI file: key, gestures, and per-measure chords."""
    return Analysis(
        key=_detect_key(parsed),
        gestures=_classify_gestures(parsed),
        chords=_chords_by_measure(parsed),
    )


# ---------------------------------------------------------------------------
# Key detection
# ---------------------------------------------------------------------------

_MIN_NOTE_QL = 0.0625  # 16th note — minimum quarter-length fed to music21 (avoids zero-length notes)


def _detect_key(parsed: ParsedMidi) -> str:
    """Detect the musical key using music21's Krumhansl-Schmuckler algorithm."""
    s = music21.stream.Stream()
    for n in parsed.notes:
        m21 = music21.note.Note(n.pitch)
        m21.quarterLength = max(n.duration_beat, _MIN_NOTE_QL)
        s.append(m21)  # key detection needs pitch+duration only, not position

    k = s.analyze("key")
    return f"{k.tonic.name} {k.mode}"


# ---------------------------------------------------------------------------
# Gesture classification — what is the instrument doing at each moment?
# ---------------------------------------------------------------------------

_GRID = 0.5       # 8th-note resolution
_MIN_DURATION = 0.5  # drop gestures shorter than an 8th note (noise/transients)


def _classify_gestures(parsed: ParsedMidi) -> list[Gesture]:
    """Classify note events into melody, dyad, or strum gestures.

    Groups note attacks by 8th-note grid slot, classifies by simultaneous pitch count,
    then merges consecutive slots with identical kind and pitches.
    """
    # 1. Group notes by attack slot (snapped to 8th-note grid)
    attacks: dict[float, list[Note]] = defaultdict(list)
    for n in parsed.notes:
        slot = round(n.start_beat / _GRID) * _GRID
        attacks[slot].append(n)

    # 2. Classify each slot
    raw: list[Gesture] = []
    for slot in sorted(attacks):
        notes = attacks[slot]
        pitches = sorted(set(n.pitch for n in notes))
        duration = max(n.duration_beat for n in notes)

        if len(pitches) == 1:
            kind, symbol = GestureKind.MELODY, None
        elif len(pitches) == 2:
            kind, symbol = GestureKind.DYAD, None
        else:
            kind, symbol = GestureKind.STRUM, _chord_symbol(tuple(pitches))

        raw.append(Gesture(kind=kind, start_beat=slot, duration_beat=duration,
                           pitches=pitches, symbol=symbol))

    # 3. Merge consecutive gestures with same kind + pitches; drop short ones
    merged: list[Gesture] = []
    for g in raw:
        if merged and merged[-1].kind == g.kind and merged[-1].pitches == g.pitches:
            merged[-1] = replace(merged[-1], duration_beat=merged[-1].duration_beat + _GRID)
        elif g.duration_beat >= _MIN_DURATION:
            merged.append(g)

    return merged


# ---------------------------------------------------------------------------
# Chord grouping — one chord symbol per measure
# ---------------------------------------------------------------------------

def _chords_by_measure(parsed: ParsedMidi) -> list[MeasureChord]:
    """Group all notes by measure and infer a single chord symbol per measure."""
    bpm = parsed.beats_per_measure
    pitches_by_measure: dict[int, list[int]] = defaultdict(list)

    for n in parsed.notes:
        measure = int(n.start_beat / bpm) + 1  # 1-indexed
        pitches_by_measure[measure].append(n.pitch)

    return [
        MeasureChord(measure=m, symbol=_chord_symbol(tuple(pitches)))
        for m, pitches in sorted(pitches_by_measure.items())
    ]


_QUALITY_SUFFIX: dict[str, str] = {
    "major": "",
    "minor": "m",
    "diminished": "dim",
    "augmented": "aug",
    "dominant-seventh": "7",
    "major-seventh": "maj7",
    "minor-seventh": "m7",
    "minor-major-seventh": "mMaj7",
    "diminished-seventh": "dim7",
    "half-diminished-seventh": "m7b5",
}


@lru_cache(maxsize=256)
def _chord_symbol(pitches: tuple[int, ...]) -> str:
    """Return a chord symbol string for a set of MIDI pitches (cached by pitch tuple)."""
    try:
        chord = music21.chord.Chord(list(pitches))
        root = chord.root().name
        quality = chord.quality
    except Exception:
        return "?"
    return root + _QUALITY_SUFFIX.get(quality, f"({quality})")
