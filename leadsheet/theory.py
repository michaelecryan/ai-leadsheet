"""Roman numeral analysis — converts key + chord symbols to scale degree notation.

Given a key string (e.g. "G major") and a list of chord symbols (e.g. ["Em", "C", "G", "D"]),
produces Roman numerals (e.g. ["vi", "IV", "I", "V"]) suitable for passing to Claude.
"""

from __future__ import annotations

# Semitone values for all note names the pipeline can produce
_NOTE_TO_SEMITONE: dict[str, int] = {
    "C": 0,  "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4,  "Fb": 4,
    "F": 5,  "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "Bb": 10, "A#": 10,
    "B": 11, "Cb": 11,
}

# Chromatic scale degrees (uppercase; caller lowercases for minor chords)
_INTERVAL_TO_NUMERAL: dict[int, str] = {
    0: "I", 1: "bII", 2: "II", 3: "bIII", 4: "III",
    5: "IV", 6: "bV", 7: "V", 8: "bVI", 9: "VI",
    10: "bVII", 11: "VII",
}

# Two-character roots the parser should match before falling back to single-char
_TWO_CHAR_ROOTS = {n for n in _NOTE_TO_SEMITONE if len(n) == 2}


def _parse_chord(symbol: str) -> tuple[str, str]:
    """Return (root, 'major'|'minor') from a chord symbol like 'Em', 'C#m', 'Bb'."""
    if len(symbol) >= 2 and symbol[:2] in _TWO_CHAR_ROOTS:
        root, rest = symbol[:2], symbol[2:]
    else:
        root, rest = symbol[0], symbol[1:]
    quality = "minor" if rest.startswith("m") else "major"
    return root, quality


def chord_to_roman(key_root: str, chord_symbol: str) -> str:
    """Convert a chord symbol to its Roman numeral relative to the given key root.

    Uses uppercase for major chords (I, IV, V) and lowercase for minor (ii, vi).
    Chromatic chords outside the diatonic scale are prefixed with 'b' or '#'.
    """
    chord_root, chord_quality = _parse_chord(chord_symbol)
    key_semi = _NOTE_TO_SEMITONE.get(key_root, 0)
    chord_semi = _NOTE_TO_SEMITONE.get(chord_root, 0)
    interval = (chord_semi - key_semi) % 12
    numeral = _INTERVAL_TO_NUMERAL.get(interval, "?")
    return numeral.lower() if chord_quality == "minor" else numeral


def analyse_progression(key: str, chord_symbols: list[str]) -> dict:
    """Return progression data for passing to the Claude lesson generator.

    Returns a dict with:
      - key_root: str (e.g. "G")
      - key_mode: str ("major" or "minor")
      - unique_chords: list[str] — chords in order of first appearance, deduped
      - roman_numerals: list[str] — matching Roman numerals
    """
    parts = key.split()
    key_root = parts[0] if parts else "C"
    key_mode = parts[1] if len(parts) > 1 else "major"

    seen: set[str] = set()
    unique_chords: list[str] = []
    for sym in chord_symbols:
        if sym not in seen:
            seen.add(sym)
            unique_chords.append(sym)

    roman_numerals = [chord_to_roman(key_root, sym) for sym in unique_chords]

    return {
        "key_root": key_root,
        "key_mode": key_mode,
        "unique_chords": unique_chords,
        "roman_numerals": roman_numerals,
    }
