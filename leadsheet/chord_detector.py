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

# Scale degree intervals (semitones from root) for diatonic triad quality lookup
_MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]
# Chord quality per scale degree (major key: I ii iii IV V vi vii°→m)
_MAJOR_QUALITIES = ['', 'm', 'm', '', '', 'm', 'm']
# Chord quality per scale degree (natural minor: i ii°→m III iv v VI VII)
_MINOR_QUALITIES = ['m', 'm', '', 'm', 'm', '', '']

_DIATONIC_BIAS = 0.06  # added to cosine score for diatonic chords


def _diatonic_chords(key: str) -> set[str]:
    """Return the set of chord symbols diatonic to the given key string (e.g. 'A minor')."""
    parts = key.split()
    if len(parts) < 2:
        return set()
    root_name, mode = parts[0], parts[1]
    if root_name not in NOTE_NAMES:
        return set()
    root = NOTE_NAMES.index(root_name)
    if mode == 'major':
        return {
            NOTE_NAMES[(root + interval) % 12] + quality
            for interval, quality in zip(_MAJOR_SCALE, _MAJOR_QUALITIES)
        }
    elif mode == 'minor':
        return {
            NOTE_NAMES[(root + interval) % 12] + quality
            for interval, quality in zip(_MINOR_SCALE, _MINOR_QUALITIES)
        }
    return set()


def _detect_chord(chroma: np.ndarray, diatonic: set[str] | None = None) -> str:
    """Match a 12-bin chroma vector to the best-fitting major/minor chord template.

    If a diatonic set is provided, chords within the key receive a small score
    bonus (_DIATONIC_BIAS) to resolve ambiguous major/minor cases toward the
    harmonically expected quality.
    """
    c = chroma / (np.linalg.norm(chroma) + 1e-9)
    best_chord, best_score = 'C', -np.inf
    for name, template in _TEMPLATES.items():
        score = float(np.dot(c, template))
        if diatonic and name in diatonic:
            score += _DIATONIC_BIAS
        if score > best_score:
            best_score = score
            best_chord = name
    return best_chord


def _smooth_chords(symbols: list[str]) -> list[str]:
    """Remove isolated single-bar chord anomalies.

    If a bar's chord differs from both its immediate neighbours (which agree
    with each other), replace it with the neighbour chord. This eliminates
    flickering caused by one bar of ambiguous chroma without affecting
    genuine chord changes.
    """
    if len(symbols) < 3:
        return symbols
    result = list(symbols)
    for i in range(1, len(symbols) - 1):
        if result[i - 1] == result[i + 1] and result[i] != result[i - 1]:
            result[i] = result[i - 1]
    return result


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

    # 2. Beat tracking — extract tempo and beat frame positions.
    # Uses the full signal (y) — beat_track relies on percussive transients.
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=_SR, units='frames')
    bpm = float(np.atleast_1d(tempo)[0])

    # 3. Harmonic-percussive source separation (HPSS).
    # Drum hits and transients create broadband spectral bursts that activate all
    # 12 chroma bins simultaneously, raising a noise floor that competes with the
    # true harmonic content. Stripping them before chroma extraction significantly
    # reduces false chord detections, especially in drum-heavy bars.
    y_harmonic, _ = librosa.effects.hpss(y)

    # 4. Constant-Q chromagram on the harmonic-only signal.
    chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=_SR)  # shape: (12, n_frames)

    # 5. Clamp near-zero energy frames before beat-sync.
    # Quiet passages (intros, fade-outs) produce near-zero chroma vectors whose
    # cosine similarity scores are dominated by noise. L2 normalization with a
    # minimum threshold suppresses these frames; fill=True replaces them with a
    # uniform distribution (1/√12 per bin) which the downstream median aggregation
    # averages away harmlessly.
    chroma = librosa.util.normalize(chroma, norm=2, threshold=1e-3, fill=True)

    # 6. Beat-synchronous chroma: median chroma within each inter-beat interval
    beat_chroma = librosa.util.sync(chroma, beat_frames, aggregate=np.median)
    # shape: (12, n_beats)

    # 7. Key detection from whole-song chroma mean (needed for diatonic bias below)
    key = _detect_key(chroma.mean(axis=1))
    diatonic = _diatonic_chords(key)

    # 8. Group beats into measures; detect one chord per measure
    n_beats = beat_chroma.shape[1]
    symbols: list[str] = []
    for bar_start in range(0, n_beats, _BEATS_PER_BAR):
        bar_chroma = beat_chroma[:, bar_start : bar_start + _BEATS_PER_BAR]
        if bar_chroma.shape[1] == 0:
            break
        measure_chroma = bar_chroma.mean(axis=1)
        symbols.append(_detect_chord(measure_chroma, diatonic=diatonic))

    # 9. Smooth out isolated single-bar anomalies (e.g. F Fm F → F F F)
    symbols = _smooth_chords(symbols)

    chords: list[MeasureChord] = [
        MeasureChord(measure=i + 1, symbol=sym) for i, sym in enumerate(symbols)
    ]

    # 10. Synthetic ParsedMidi — carries tempo + time-sig metadata for the backend
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
