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

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']

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


def _detect_key(chroma_mean: np.ndarray, first_chord: str | None = None) -> str:
    """Estimate key from mean chroma using Krumhansl-Schmuckler correlation.

    When `first_chord` is provided, the top-8 K-S candidates are scanned for
    one whose tonic chord matches the first detected chord of the song. Songs
    almost always start on the tonic, so this reliably resolves the common
    failure mode where K-S returns a relative-key false positive
    (e.g. 'F major' for an Am G F C song that is actually in A minor).

    Falls back to the raw K-S winner if no candidate's tonic matches.
    """
    c = chroma_mean - chroma_mean.mean()
    scores: list[tuple[float, str]] = []
    for i, name in enumerate(NOTE_NAMES):
        for mode, profile in (('major', _KS_MAJOR), ('minor', _KS_MINOR)):
            p = np.roll(profile, i)
            p = p - p.mean()
            r = float(np.dot(c, p) / (np.linalg.norm(c) * np.linalg.norm(p) + 1e-9))
            scores.append((r, f'{name} {mode}'))
    scores.sort(reverse=True)

    if first_chord:
        # Prefer whichever top-8 key has `first_chord` as its tonic (I or i).
        for _, key in scores[:8]:
            root, mode = key.split()
            tonic = root if mode == 'major' else root + 'm'
            if first_chord == tonic:
                return key

    return scores[0][1]


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


def _disambiguate_relative_key(key: str, raw_symbols: list[str]) -> str:
    """Resolve relative major/minor ambiguity using chord-content heuristics.

    The Krumhansl-Schmuckler algorithm struggles to distinguish relative major/minor
    pairs because they share the same pitch classes. A song in A minor (Am, G, F, C)
    can outscore A minor with F major because F, C, G, and A are all diatonic to F.

    Two signals disambiguate:
    1. The first chord of a song is almost always the tonic — if it's the relative
       minor tonic (e.g. Am when the key is F major), prefer the minor key.
    2. The relative minor tonic must appear at least as often as the major tonic —
       guards against songs that genuinely start on the vi chord in a major key.

    Only applied when K-S returns major; minor detections are typically correct.
    """
    if not raw_symbols:
        return key
    parts = key.split()
    if len(parts) < 2 or parts[1] != 'major':
        return key

    root = NOTE_NAMES.index(parts[0])
    rel_minor_root = NOTE_NAMES[(root + 9) % 12]  # e.g. F → A
    minor_tonic = rel_minor_root + 'm'             # e.g. 'Am'

    first_is_minor = raw_symbols[0] == minor_tonic
    major_count = raw_symbols.count(parts[0])
    minor_count = raw_symbols.count(minor_tonic)

    # Switch to relative minor if the first chord is the minor tonic and it
    # appears at least 60% as often as the major tonic chord. The 0.6 threshold
    # handles songs where the major tonic chord appears in extended sections
    # (e.g. a bridge of sustained F chords) while the true tonal centre is the
    # relative minor. A genuine F major song would have Am appear far less often.
    if first_is_minor and minor_count >= major_count * 0.6:
        return f'{rel_minor_root} minor'
    return key


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

_SR_HIRES = 22050    # high sample rate for key detection (first 30s) — preserves full harmonics
_SR_LORES = 11025    # low sample rate for chord detection — filters HF noise, halves memory
_BEATS_PER_BAR = 4   # assume 4/4 — covers the vast majority of AI-generated music
_KEY_DURATION = 30   # seconds at high SR for accurate key/first-chord detection
_MAX_DURATION = 180  # seconds at low SR for full-song chord coverage


def detect_chords_librosa(path: Path) -> tuple[ParsedMidi, Analysis]:
    """Load audio and detect chords via two-stage beat-synchronous chromagram matching.

    Stage 1 (key detection): First 30s at 22050 Hz — high resolution preserves
    the full harmonic spectrum needed for accurate first-chord and key detection.

    Stage 2 (chord detection): Full song at 11025 Hz — lower sample rate filters
    high-frequency noise from rich productions (Suno v5, heavy distortion) while
    keeping memory within Railway's 512 MB constraint.

    Returns a (ParsedMidi, Analysis) pair compatible with the rest of the pipeline.
    """
    import gc

    # ── Stage 1: Key detection from first 30s at high resolution ──────────
    y_hi, _ = librosa.load(str(path), sr=_SR_HIRES, mono=True, duration=_KEY_DURATION)
    y_harm_hi, _ = librosa.effects.hpss(y_hi)
    chroma_hi = librosa.feature.chroma_cqt(y=y_harm_hi, sr=_SR_HIRES)
    chroma_hi = librosa.util.normalize(chroma_hi, norm=2, threshold=1e-3, fill=True)

    # Beat-sync the high-res chroma to detect the first chord accurately
    _, beat_frames_hi = librosa.beat.beat_track(y=y_hi, sr=_SR_HIRES, units='frames')
    beat_chroma_hi = librosa.util.sync(chroma_hi, beat_frames_hi, aggregate=np.median)

    n_beats_hi = beat_chroma_hi.shape[1]
    raw_symbols_hi: list[str] = []
    for bar_start in range(0, n_beats_hi, _BEATS_PER_BAR):
        bar_chroma = beat_chroma_hi[:, bar_start : bar_start + _BEATS_PER_BAR]
        if bar_chroma.shape[1] == 0:
            break
        raw_symbols_hi.append(_detect_chord(bar_chroma.mean(axis=1)))

    first_chord = raw_symbols_hi[0] if raw_symbols_hi else None
    key = _detect_key(chroma_hi.mean(axis=1), first_chord=first_chord)
    diatonic = _diatonic_chords(key)

    # Free all stage 1 data before loading the full song
    del y_hi, y_harm_hi, chroma_hi, beat_chroma_hi, beat_frames_hi
    gc.collect()

    # ── Stage 2: Full-song chord detection at low resolution ──────────────
    y, _ = librosa.load(str(path), sr=_SR_LORES, mono=True, duration=_MAX_DURATION)

    # Beat tracking on full signal (needs percussive transients)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=_SR_LORES, units='frames')
    bpm = float(np.atleast_1d(tempo)[0])

    # HPSS — strip drums before chroma extraction
    y_harmonic, _ = librosa.effects.hpss(y)
    del y  # free raw signal — only harmonic needed from here
    gc.collect()

    # Constant-Q chromagram on harmonic-only signal
    chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=_SR_LORES)
    del y_harmonic
    gc.collect()

    # Clamp near-zero energy frames
    chroma = librosa.util.normalize(chroma, norm=2, threshold=1e-3, fill=True)

    # Beat-synchronous chroma (median per beat interval)
    beat_chroma = librosa.util.sync(chroma, beat_frames, aggregate=np.median)

    # Chord detection with diatonic bias from stage 1's key
    n_beats = beat_chroma.shape[1]
    symbols: list[str] = []
    for bar_start in range(0, n_beats, _BEATS_PER_BAR):
        bar_chroma = beat_chroma[:, bar_start : bar_start + _BEATS_PER_BAR]
        if bar_chroma.shape[1] == 0:
            break
        symbols.append(_detect_chord(bar_chroma.mean(axis=1), diatonic=diatonic))

    # Smooth out isolated single-bar anomalies (e.g. F Fm F → F F F)
    symbols = _smooth_chords(symbols)

    chords: list[MeasureChord] = [
        MeasureChord(measure=i + 1, symbol=sym) for i, sym in enumerate(symbols)
    ]

    # 12. Synthetic ParsedMidi — carries tempo + time-sig metadata for the backend
    # Guard against BPM=0 (can happen with very short or silent audio)
    if bpm <= 0:
        raise ValueError("Could not detect a tempo — the audio may be too short or silent.")
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
