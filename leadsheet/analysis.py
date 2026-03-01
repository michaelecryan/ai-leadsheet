from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

import music21

from leadsheet.midi import Note, ParsedMidi


@dataclass
class MeasureChord:
    measure: int    # 1-indexed
    symbol: str     # e.g. "Em", "Cmaj7", "G"


@dataclass
class Gesture:
    kind: Literal["melody", "dyad", "strum"]
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
    return Analysis(
        key=_detect_key(parsed),
        gestures=_classify_gestures(parsed),
        chords=_chords_by_measure(parsed),
    )


# ---------------------------------------------------------------------------
# Key detection
# ---------------------------------------------------------------------------

def _detect_key(parsed: ParsedMidi) -> str:
    s = music21.stream.Stream()
    for n in parsed.notes:
        m21 = music21.note.Note(n.pitch)
        m21.quarterLength = max(n.duration_beat, 0.0625)  # avoid zero-length
        s.append(m21)  # key detection needs pitch+duration only, not position

    k = s.analyze("key")
    return f"{k.tonic.name} {k.mode}"


# ---------------------------------------------------------------------------
# Gesture classification — what is the instrument doing at each moment?
# ---------------------------------------------------------------------------

_GRID = 0.5       # 8th-note resolution
_MIN_DURATION = 0.5  # drop gestures shorter than an 8th note (noise/transients)


def _classify_gestures(parsed: ParsedMidi) -> list[Gesture]:
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
            kind: Literal["melody", "dyad", "strum"] = "melody"
            symbol = None
        elif len(pitches) == 2:
            kind = "dyad"
            symbol = None
        else:
            kind = "strum"
            symbol = _chord_symbol(music21.chord.Chord(pitches))

        raw.append(Gesture(kind=kind, start_beat=slot, duration_beat=duration,
                           pitches=pitches, symbol=symbol))

    # 3. Merge consecutive gestures with same kind + pitches
    merged: list[Gesture] = []
    for g in raw:
        if merged and merged[-1].kind == g.kind and merged[-1].pitches == g.pitches:
            prev = merged[-1]
            merged[-1] = Gesture(kind=prev.kind, start_beat=prev.start_beat,
                                 duration_beat=prev.duration_beat + _GRID,
                                 pitches=prev.pitches, symbol=prev.symbol)
        else:
            merged.append(g)

    # 4. Drop very short gestures (transients / mix bleed)
    return [g for g in merged if g.duration_beat >= _MIN_DURATION]


# ---------------------------------------------------------------------------
# Chord grouping — one chord symbol per measure
# ---------------------------------------------------------------------------

def _chords_by_measure(parsed: ParsedMidi) -> list[MeasureChord]:
    bpm = parsed.beats_per_measure
    pitches_by_measure: dict[int, list[int]] = defaultdict(list)

    for n in parsed.notes:
        measure = int(n.start_beat / bpm) + 1  # 1-indexed
        pitches_by_measure[measure].append(n.pitch)

    return [
        MeasureChord(measure=m, symbol=_chord_symbol(music21.chord.Chord(pitches)))
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


def _chord_symbol(chord: music21.chord.Chord) -> str:
    try:
        root = chord.root().name
        quality = chord.quality
    except Exception:
        return "?"
    return root + _QUALITY_SUFFIX.get(quality, f"({quality})")
