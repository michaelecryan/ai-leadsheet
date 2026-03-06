"""Beat-synchronous chord detection via librosa chromagram + template matching.

Alternative to the Basic Pitch → MIDI → music21 pipeline.

Instead of transcribing individual notes, this module analyses harmonic content
directly using chroma features — the standard approach in academic chord recognition.

Advantages over Basic Pitch for chord detection:
  - Chromagram captures ALL harmonic content regardless of timbre or playing style
  - Beat-synchronous output: chord changes snap to rhythmic grid
  - No neural network inference, so faster and memory-light
  - Works equally well on AI-generated audio (Suno/Udio) and any other genre

Usage (set env var to activate):
  CHORD_DETECTOR=librosa uv run uvicorn backend.main:app --reload
"""

from __future__ import annotations

import numpy as np
from pathlib import Path

import librosa

from leadsheet.analysis import Analysis, MeasureChord
from leadsheet.midi import ParsedMidi


# ---------------------------------------------------------------------------
# Chord templates (12-bin chroma, C = index 0)
# ---------------------------------------------------------------------------

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Root-position triads: [root, 3rd, 5th]
_MAJOR_TRIAD = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0], dtype=float)  # root, maj 3rd, P5
_MINOR_TRIAD = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0], dtype=float)  # root, min 3rd, P5


def _build_templates() -> dict[str, np.ndarray]:
    """Build normalized chord templates for 12 major and 12 minor triads."""
    templates: dict[str, np.ndarray] = {}
    for i, name in enumerate(NOTE_NAMES):
        maj = np.roll(_MAJOR_TRIAD, i)
        templates[name] = maj / np.linalg.norm(maj)
        min_ = np.roll(_MINOR_TRIAD, i)
        templates[name + 'm'] = min_ / np.linalg.norm(min_)
    return templates


_TEMPLATES = _build_templates()


# ---------------------------------------------------------------------------
# Key detection — Krumhansl-Schmuckler profiles
# ---------------------------------------------------------------------------

# Tonal hierarchy weights from Krumhansl & Schmuckler (1990)
_KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def _detect_key(chroma_mean: np.ndarray) -> str:
    """Estimate key from mean chroma using Krumhansl-Schmuckler correlation."""
    c = chroma_mean - chroma_mean.mean()
    best_key, best_r = 'C major', -np.inf
    for i, name in enumerate(NOTE_NAMES):
        for mode, profile in (('major', _KS_MAJOR), ('minor', _KS_MINOR)):
            p = np.roll(profile, i)
            p = p - p.mean()
            r = np.dot(c, p) / (np.linalg.norm(c) * np.linalg.norm(p) + 1e-9)
            if r > best_r:
                best_r = r
                best_key = f'{name} {mode}'
    return best_key


# ---------------------------------------------------------------------------
# Chord detection — cosine similarity to templates
# ---------------------------------------------------------------------------

def _detect_chord(chroma: np.ndarray) -> str:
    """Match a 12-bin chroma vector to the best-fitting major/minor chord template."""
    c = chroma / (np.linalg.norm(chroma) + 1e-9)
    best_chord, best_score = 'C', -np.inf
    for name, template in _TEMPLATES.items():
        score = float(np.dot(c, template))
        if score > best_score:
            best_score = score
            best_chord = name
    return best_chord


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

_SR = 22050          # sample rate for analysis (librosa default)
_BEATS_PER_BAR = 4   # assume 4/4 — covers the vast majority of AI-generated music


def detect_chords_librosa(path: Path) -> tuple[ParsedMidi, Analysis]:
    """Load audio and detect chords via beat-synchronous chromagram matching.

    Returns a (ParsedMidi, Analysis) pair compatible with the rest of the pipeline.
    The ParsedMidi contains tempo + time-sig metadata but no MIDI notes (they are
    not used downstream when this path is active).
    """
    # 1. Load audio as mono at analysis sample rate
    y, _ = librosa.load(str(path), sr=_SR, mono=True)

    # 2. Beat tracking — extract tempo and beat frame positions
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=_SR, units='frames')
    bpm = float(np.atleast_1d(tempo)[0])

    # 3. Constant-Q chromagram (better harmonic resolution than STFT chroma)
    chroma = librosa.feature.chroma_cqt(y=y, sr=_SR)  # shape: (12, n_frames)

    # 4. Beat-synchronous chroma: median chroma within each inter-beat interval
    beat_chroma = librosa.util.sync(chroma, beat_frames, aggregate=np.median)
    # shape: (12, n_beats)

    # 5. Group beats into measures; detect one chord per measure
    n_beats = beat_chroma.shape[1]
    chords: list[MeasureChord] = []
    for bar_start in range(0, n_beats, _BEATS_PER_BAR):
        bar_chroma = beat_chroma[:, bar_start : bar_start + _BEATS_PER_BAR]
        if bar_chroma.shape[1] == 0:
            break
        measure_chroma = bar_chroma.mean(axis=1)
        symbol = _detect_chord(measure_chroma)
        measure_num = bar_start // _BEATS_PER_BAR + 1
        chords.append(MeasureChord(measure=measure_num, symbol=symbol))

    # 6. Key detection from whole-song chroma mean
    key = _detect_key(chroma.mean(axis=1))

    # 7. Synthetic ParsedMidi — carries tempo + time-sig metadata for the backend
    tempo_us = int(60_000_000 / bpm)
    parsed = ParsedMidi(
        ticks_per_beat=480,
        tempo=tempo_us,
        time_sig_numerator=_BEATS_PER_BAR,
        time_sig_denominator=4,
        notes=[],
    )

    result = Analysis(key=key, gestures=[], chords=chords)
    return parsed, result
