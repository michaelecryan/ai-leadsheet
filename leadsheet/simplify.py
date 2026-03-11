"""Simplification — strip jazz extensions, normalize enharmonics, and suggest capo positions."""

from __future__ import annotations

from dataclasses import dataclass

from leadsheet.analysis import Analysis, MeasureChord


@dataclass
class Simplified:
    key: str                    # Normalized key, e.g. "E major"
    chords: list[MeasureChord]  # Simplified chord symbols
    capo: int | None            # Suggested capo fret, or None
    capo_shape_key: str | None  # Shape key to play in, e.g. "A" (when capo is set)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def simplify(result: Analysis) -> Simplified:
    """Apply guitar-friendly simplification: normalize key, strip extensions, suggest capo."""
    key = _normalize_key(result.key)
    chords = [MeasureChord(c.measure, _simplify_chord(c.symbol)) for c in result.chords]
    capo = _suggest_capo(key)
    capo_shape_key = None
    if capo is not None:
        semitone = _PITCH_TO_SEMITONE.get(key.split()[0], 0)
        capo_shape_key = _SEMITONE_TO_NAME[(semitone - capo) % 12]
    return Simplified(key=key, chords=chords, capo=capo, capo_shape_key=capo_shape_key)


# ---------------------------------------------------------------------------
# Pitch / key utilities
# ---------------------------------------------------------------------------

# Semitone values (C=0), covering all common names including music21's "-" flat notation
_PITCH_TO_SEMITONE: dict[str, int] = {
    "C": 0,  "B#": 0,
    "C#": 1, "D-": 1,
    "D": 2,
    "D#": 3, "E-": 3,
    "E": 4,  "F-": 4,
    "F": 5,  "E#": 5,
    "F#": 6, "G-": 6,
    "G": 7,
    "G#": 8, "A-": 8,
    "A": 9,
    "A#": 10, "B-": 10,
    "B": 11, "C-": 11,
}

# Sharp-preferring spelling at each semitone (guitar standard)
_SEMITONE_TO_NAME: dict[int, str] = {
    0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "Bb", 11: "B",
}

# Semitone values for keys that feel natural on guitar with open chords
_FRIENDLY_MAJOR = {0, 2, 4, 7, 9}   # C D E G A
_FRIENDLY_MINOR = {9, 4, 2, 11}     # Am Em Dm Bm


def _normalize_key(key: str) -> str:
    """Convert enharmonic key spelling to guitar-friendly (sharp-preferring)."""
    tonic, mode = key.split(" ", 1)
    semitone = _PITCH_TO_SEMITONE.get(tonic, 0)
    return f"{_SEMITONE_TO_NAME[semitone]} {mode}"


# ---------------------------------------------------------------------------
# Chord simplification
# ---------------------------------------------------------------------------

# Ordered so longer suffixes match first (e.g. "maj13" before "13")
_EXTENSION_STRIP: list[tuple[str, str]] = [
    ("maj13", "maj7"), ("maj11", "maj7"), ("maj9", "maj7"),
    ("m13",   "m7"),   ("m11",   "m7"),   ("m9",   "m7"),
    ("13",    "7"),    ("11",    "7"),    ("9",    "7"),
]


def _simplify_chord(symbol: str) -> str:
    """Reduce a chord symbol to a guitar-playable form (strip extensions, fix enharmonics)."""
    # Slash chords → root only: "C/E" → "C"
    if "/" in symbol:
        symbol = symbol.split("/")[0]

    # Normalize music21 flat-root notation: "G-m" → "F#m"
    if len(symbol) >= 2 and symbol[1] == "-":
        semitone = _PITCH_TO_SEMITONE.get(symbol[:2])
        if semitone is not None:
            symbol = _SEMITONE_TO_NAME[semitone] + symbol[2:]

    # Collapse diminished chords to nearest playable neighbour (dim → minor)
    if "dim7" in symbol:
        return symbol.replace("dim7", "m7")
    if "dim" in symbol:
        return symbol.replace("dim", "m")

    # Unknown quality (our fallback wraps in parens) → strip to triad
    if "(" in symbol:
        return symbol.split("(")[0]

    # Strip extensions beyond 7th
    for ext, replacement in _EXTENSION_STRIP:
        if symbol.endswith(ext):
            return symbol[: -len(ext)] + replacement

    return symbol


# ---------------------------------------------------------------------------
# Capo suggestion
# ---------------------------------------------------------------------------

def _suggest_capo(key: str) -> int | None:
    """Return the lowest capo fret that puts the key into a guitar-friendly shape key.

    Capo N means the player uses shapes N semitones below the actual key.
    e.g. Bb major + capo 1 → play A major shapes.
    """
    tonic, mode = key.split(" ", 1)
    semitone = _PITCH_TO_SEMITONE.get(tonic, 0)
    friendly = _FRIENDLY_MAJOR if mode == "major" else _FRIENDLY_MINOR

    if semitone in friendly:
        return None

    for capo in range(1, 8):  # practical capo range: frets 1–7
        if (semitone - capo) % 12 in friendly:
            return capo

    return None
