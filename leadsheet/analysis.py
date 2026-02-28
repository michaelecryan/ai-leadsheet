from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import music21

from leadsheet.midi import Note, ParsedMidi


@dataclass
class MeasureChord:
    measure: int    # 1-indexed
    symbol: str     # e.g. "Em", "Cmaj7", "G"


@dataclass
class Analysis:
    key: str                    # e.g. "E major"
    melody: list[Note]          # top-voice note line
    chords: list[MeasureChord]  # one chord symbol per measure


def analyse(parsed: ParsedMidi) -> Analysis:
    return Analysis(
        key=_detect_key(parsed),
        melody=_extract_melody(parsed),
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
# Melody extraction — highest pitch per 8th-note slot, merged + filtered
# ---------------------------------------------------------------------------

_GRID = 0.5   # 8th-note resolution
_MIN_DURATION = 0.5  # drop notes shorter than an 8th note (noise/transients)


def _extract_melody(parsed: ParsedMidi) -> list[Note]:
    # 1. Highest pitch at each 8th-note grid slot
    grid: dict[float, Note] = {}
    for n in parsed.notes:
        slot = round(n.start_beat / _GRID) * _GRID
        if slot not in grid or n.pitch > grid[slot].pitch:
            grid[slot] = n

    slots = sorted(grid)

    # 2. Merge consecutive slots with the same pitch into one longer note
    merged: list[Note] = []
    for slot in slots:
        n = grid[slot]
        if merged and merged[-1].pitch == n.pitch:
            prev = merged[-1]
            merged[-1] = Note(
                pitch=prev.pitch,
                start_beat=prev.start_beat,
                duration_beat=prev.duration_beat + _GRID,
                velocity=prev.velocity,
                channel=prev.channel,
            )
        else:
            merged.append(Note(
                pitch=n.pitch,
                start_beat=slot,
                duration_beat=_GRID,
                velocity=n.velocity,
                channel=n.channel,
            ))

    # 3. Drop very short notes (transients / mix bleed)
    return [n for n in merged if n.duration_beat >= _MIN_DURATION]


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
