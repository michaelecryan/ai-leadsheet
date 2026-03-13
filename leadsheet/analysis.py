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
    ARPEGGIO = "arpeggio"


@dataclass
class MeasureChord:
    measure: int              # 1-indexed
    symbol: str               # e.g. "Em", "Cmaj7", "G"
    time_seconds: float | None = None  # actual start time; set by chord_detector, None for MIDI path


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

# Guitar practical pitch range — notes outside this are overtones or sub-bass noise.
# E2 (MIDI 40) = open low E string; B4 (MIDI 71) = 7th fret high e string (readable in treble clef).
_MIN_PITCH = 52   # E3 — lowest note readable in treble clef without excessive ledger lines
_MAX_PITCH = 76   # E5 — upper limit before overtone territory for acoustic guitar

# Arpeggio detection thresholds
_ARP_MAX_GAP_BEATS = 1.0    # max start-to-start gap between consecutive picks (≤ quarter note)
_ARP_WINDOW_BEATS = 4.0     # max total span of a run (one 4/4 measure)
_ARP_MIN_PITCH_CLASSES = 3  # min distinct pitch classes to form a chord (2 = harmonically ambiguous)


def _detect_arpeggios(gestures: list[Gesture]) -> list[Gesture]:
    """Collapse runs of consecutive MELODY gestures that form a recognizable chord.

    Scans for contiguous MELODY runs where consecutive attacks are within
    _ARP_MAX_GAP_BEATS and the total span is within _ARP_WINDOW_BEATS. If the
    combined pitch classes number at least _ARP_MIN_PITCH_CLASSES and produce a
    clean chord symbol, the run collapses into a single ARPEGGIO gesture.
    """
    result: list[Gesture] = []
    window: list[Gesture] = []

    def flush_window() -> None:
        if len(window) < 2:
            result.extend(window)
            window.clear()
            return

        all_pitches = [p for g in window for p in g.pitches]
        pitch_classes = tuple(sorted(set(p % 12 for p in all_pitches)))

        if len(pitch_classes) < _ARP_MIN_PITCH_CLASSES:
            result.extend(window)
            window.clear()
            return

        # Pass pitch classes (not full MIDI pitches) to maximise lru_cache hits
        # across different octave voicings of the same chord.
        symbol = _chord_symbol(pitch_classes)
        if symbol == "?" or "(" in symbol:
            result.extend(window)
            window.clear()
            return

        first, last = window[0], window[-1]
        result.append(Gesture(
            kind=GestureKind.ARPEGGIO,
            start_beat=first.start_beat,
            duration_beat=(last.start_beat + last.duration_beat) - first.start_beat,
            pitches=sorted(set(all_pitches)),
            symbol=symbol,
        ))
        window.clear()

    for g in gestures:
        if g.kind != GestureKind.MELODY:
            flush_window()
            result.append(g)
            continue

        if window:
            gap = g.start_beat - window[-1].start_beat   # start-to-start, handles sustain
            span = g.start_beat - window[0].start_beat
            if gap > _ARP_MAX_GAP_BEATS or span > _ARP_WINDOW_BEATS:
                flush_window()

        window.append(g)

    flush_window()
    return result


def _classify_gestures(parsed: ParsedMidi) -> list[Gesture]:
    """Classify note events into melody, dyad, or strum gestures.

    Groups note attacks by 8th-note grid slot, classifies by simultaneous pitch count,
    then merges consecutive slots with identical kind and pitches.
    """
    # 1. Group notes by attack slot (snapped to 8th-note grid), filtered to guitar range
    attacks: dict[float, list[Note]] = defaultdict(list)
    for n in parsed.notes:
        if not (_MIN_PITCH <= n.pitch <= _MAX_PITCH):
            continue
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

    return _detect_arpeggios(merged)


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


# Guitar-friendly scale suggestions keyed by (tonic, mode)
_GUITAR_SCALES: dict[tuple[str, str], list[str]] = {
    ("A", "minor"): ["A minor pentatonic", "A natural minor"],
    ("E", "minor"): ["E minor pentatonic", "E natural minor"],
    ("D", "minor"): ["D minor pentatonic", "D natural minor"],
    ("B", "minor"): ["B minor pentatonic", "B natural minor"],
    ("F#", "minor"): ["F# minor pentatonic", "F# natural minor"],
    ("C#", "minor"): ["C# minor pentatonic", "C# natural minor"],
    ("C", "major"): ["C major pentatonic", "A minor pentatonic"],
    ("G", "major"): ["G major pentatonic", "E minor pentatonic"],
    ("D", "major"): ["D major pentatonic", "B minor pentatonic"],
    ("A", "major"): ["A major pentatonic", "F# minor pentatonic"],
    ("E", "major"): ["E major pentatonic", "C# minor pentatonic"],
    ("F", "major"): ["F major pentatonic", "D minor pentatonic"],
    ("Bb", "major"): ["Bb major pentatonic", "G minor pentatonic"],
}


def suggest_scales(key: str) -> list[str]:
    """Return guitar-friendly scale suggestions for a detected key string (e.g. 'F major')."""
    tonic, mode = key.split(" ", 1)
    return _GUITAR_SCALES.get((tonic, mode), [f"{tonic} {mode}"])


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
