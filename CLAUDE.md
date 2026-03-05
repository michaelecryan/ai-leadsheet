# AI Lead Sheet — Claude Working Document

> **For Claude:** Read this entire file before writing any code. This is the source of truth.
> After reading, confirm: what is built, what is in scope for this session, and what is off-limits.

---

## What This Product Does

Takes a Suno or Udio song and turns it into a music-curious non-musician's first guitar lesson — automatically.

Upload AI song → get key (plain English) → get 3–5 chords (large finger diagrams) → play along in sync → get pointed to the right JustinGuitar / Marty Music lesson.

**Core principle: "Your AI song as your first music lesson."**

**The magic trick:** a song that sounds complex is usually 4 chords. The product reveals that simplicity in a way that feels like a revelation, not a disappointment. "Your song in 4 chords" is the hero moment.

The user is a non-musician. They do not know what a chord progression is. They do not know what Chordify is. They are motivated because it is their song. Design everything for that person.

---

## Tech Stack

- Language: Python
- Package manager: `uv` (not pip, not poetry)
- Music library: `music21`
- Audio transcription: Basic Pitch (Spotify)
- Run command: `uv run python -m leadsheet.cli generate song.mid --out chart.xml`
- Output format: MusicXML (`.xml`) — will move to browser rendering in Phase 3
- Entry point: `main.py`
- Key files: `analysis.py`, `export.py`, `audio.py`, `simplify.py`, `cli.py`

---

## Current Build State

### ✅ Built and Working
- MIDI parsing (`midi.py`) — tempo, time sig, note extraction
- Key detection (`analysis.py`) — music21 analyzer
- Gesture classifier (`analysis.py`) — melody / dyad / strum / arpeggio classification
- Chord inference by measure (`analysis.py`)
- Chord simplification (`simplify.py`) — extensions, enharmonics, slash chords
- Capo suggestion (`simplify.py`) — frets 1–7, guitar-friendly keys
- MusicXML export (`export.py`) — gesture-aware: notes, dyads, slash noteheads; treble clef forced
- CLI (`cli.py`) — Typer, --simplify/--no-simplify, --inspect, rich console output
- Audio transcription (`audio.py`) — Basic Pitch → temp MIDI → pipeline
- Pitch range filter (`analysis.py`) — strips overtones outside E2–E5 (MIDI 40–76)
- Arpeggio detection — sequential fingerpicked notes collapse into chord symbol + arpeggio mark
- Calibrated against "Idea #1 - Acoustic Alternative.mp3": chord progression correct

### 🔄 Active Development
- Web UI shell (Phase 3 — now prioritised)
- Chord output quality improvements (Essentia and Demucs evaluation in separate branch)
- Playback sync (chord highlighting during audio playback — the core "aha" feature)

### ❌ Not Started (Future Phases)
- PDF export (Phase 7)
- Accounts/auth (Phase 5)
- Payment/paywall (Phase 6)
- `--for guitar|piano` CLI flag (future phase — guitar only for V1)
- Melody tabs / fretboard mapper (Phase 8)
- Piano voicings / piano chord diagrams (later phase — guitar is V1 instrument)

---

## Input Strategy — Audio is Primary

**Audio is the primary V1 input path.** MIDI is supported and produces cleaner output,
but requires a paid Suno plan (Pro ~$10/month). Audio export is available to all free-tier
users — a significantly larger audience.

**Hero flow:** Suno/Udio free user exports MP3 → uploads to web UI → gets a playable chord chart → presses play → follows chords in sync.

**Audio quality findings (from testing):**
- Suno/Udio synthesized audio transcribes well — chord progressions correct, gestures clean
- Live acoustic guitar recordings are harder: overtones, tuning variance, chord-melody bleed
- These issues are specific to live recordings, not the primary use case

**MIDI as premium path:** Supports users on paid Suno plans who want cleaner output. Worth keeping, not the lead product story.

---

## The Core Product Loop (Keep This In Mind Always)

1. **Upload** — user drops in their Suno/Udio MP3 or WAV
2. **Understand** — key shown with plain-English explanation; 3–5 chords as large finger diagrams; "Your song in 4 chords" is the hero moment
3. **Play along** — chords highlight in sync with audio; no theory knowledge required to follow
4. **Learn** — curated JustinGuitar / Marty Music videos mapped to the chords detected in their song

Step 3 is the "aha" moment. Step 4 is the retention mechanism.

**The first 15 minutes determine everything.** The product lives or dies on this window.

**Atomic acceptance tests for V1:**
- User drops in Suno song → in under 10 seconds understands: key, 3–5 chords, where to put fingers for chord 1
- User presses play → follows highlighted chord names without any theory knowledge → feels like "I'm playing my song"
- After first play-through, user knows exactly one thing they learned (e.g. "this shape is G")

---

## Current Session Scope

**Before starting any session, the user will specify what we're working on.**
If no scope is given, ask: "What are we working on today?" before touching any code.

Do not expand scope beyond what is stated for the session.

---

## Output Contract — What a Valid Lead Sheet Contains

| Element | Included | Notes |
|---|---|---|
| Chord symbols | ✅ | Primary output — per measure |
| Key signature | ✅ | Guitar-friendly keys preferred |
| Time signature | ✅ | Detected from input |
| Chord simplification | ✅ | Extensions stripped to playable shapes |
| Capo suggestion | ✅ | When key is guitar-unfriendly |
| Melody line | 🔄 | Deprioritised — messy from Basic Pitch; may return in Phase 2 |
| Chord timestamps | ✅ | Required for playback sync |
| Full piano voicings | ❌ | Not in V1 — piano expansion planned for later phase |
| Bass line | ❌ | Never add |
| Drum parts | ❌ | Never add |
| Chord diagrams | ✅ | Core to V1 — large, simple finger diagrams for non-musicians. Rendered from chord symbols. |
| Melody tabs | Phase 4 | Requires fretboard mapper |

---

## Simplification Rules (Always Apply Unless `--no-simplify`)

| Rule | Input Example | Output |
|---|---|---|
| Strip extensions beyond 7th | Cmaj9 | Cmaj7 |
| Strip color tones | G13#11 | G7 |
| Normalize enharmonics | Gb major | F# major |
| Prefer guitar-friendly keys | Bb major | Suggest capo 1, A shapes |
| Reduce slash chords | C/E | C |

---

## Gesture Classifier — Design Reference

Built in `analysis.py`. Classifies note events into gesture types; rendered differently in `export.py`.

| Gesture | Signal | Notation | Status |
|---|---|---|---|
| Single-note line | 1 note per grid slot | Notes on staff | ✅ Done |
| Dyad / power chord | 2 simultaneous notes | Interval notation | ✅ Done |
| Chord strum | 3+ simultaneous notes | Chord symbol + slash notehead | ✅ Done |
| Arpeggio | 3–6 notes from same harmony, sequential | Chord symbol + arpeggio mark | ✅ Done |

---

## Hard Rules — Never Do These

- ❌ Do not add drum or bass output
- ❌ Do not add piano voicings or piano chord diagrams until explicitly instructed (planned for later phase, not V1)
- ❌ Do not add accounts, auth, or payment logic until Phase 4
- ❌ Do not add PDF export until Phase 7
- ❌ Do not install new dependencies without asking first
- ❌ Do not rename or restructure files without asking
- ❌ Do not rewrite working modules to "improve" them unless asked
- ❌ Do not expand audio.py without explicit instruction

---

## Code Quality Standards

- All functions must have docstrings
- New modules need a brief comment at the top explaining their role
- Don't use magic numbers — name constants
- Errors should print a clear message to the terminal, not just raise silently
- Commit after each logical unit of work with a clear commit message

---

## CLI Interface Reference

```bash
# Basic usage
uv run python -m leadsheet.cli generate song.mid --out chart.xml

# With simplification disabled
uv run python -m leadsheet.cli generate song.mid --out chart.xml --no-simplify

# Expected terminal output
Loading MIDI: song.mid
Detected Key: E major
Chord progression: E | A | B | C#m
Exported: chart.xml
```

---

## V1 Success Criteria (Definition of Done)

**Primary metric:** % of new users who complete one full play-through of their own song and engage with at least one chord.

V1 is complete when ALL of these are true:
1. User uploads Suno/Udio audio → receives key + chords in under 10 seconds
2. Chord display is immediately readable by someone who has never played guitar (large diagrams, no jargon)
3. Audio plays back with chords highlighting in sync — no theory knowledge required
4. At least one contextual lesson link (JustinGuitar / Marty) surfaced based on detected chords
5. Validated on 5–10 real Suno/Udio exports across different genres
6. Demo video posted to r/SunoAI — generates genuine comments, not just upvotes

**Early KPIs:**
- Activation: % who upload a second song within 7 days
- Learning: % who answer 1–2 simple in-app chord recognition questions correctly
- Revenue: conversion to paid after at least one "I'm actually playing" moment

---

## Roadmap Reference (Do Not Build Ahead)

| Phase | Focus | Status |
|---|---|---|
| 1 | CLI engine. Audio/MIDI in, MusicXML out. Simplification. Arpeggio detection. | ✅ Done |
| 2 | Web UI shell. FastAPI backend. Upload → key + chords displayed in browser. Large chord diagrams, plain-English key explanation. | 🔄 Active |
| 3 | Playback sync. Chords highlight in real time during audio playback. | 🔄 Active |
| 3b | Education layer. Surface contextual JustinGuitar / Marty Music YouTube lessons based on detected chords and song feel. This is the retention mechanism — do not defer past Phase 3. | 🔄 Active |
| 4 | Chord quality improvements. Essentia/Demucs pipeline evaluation. | 🔄 Active |
| 5 | User accounts + chart storage. Auth. Saved charts dashboard. | Not started |
| 6 | Monetisation. Stripe. Free/paid tier. ~$5–10/month. | Not started |
| 7 | PDF export. Formatting polish. | Not started |
| 8 | Melody tabs (fretboard mapper). Post-validation only. | Not started |

## Phase 2/3 Rendering Stack (Decided, Not Yet Built)

- **Standard notation / chord chart** — rendered client-side from MusicXML using **alphaTab** (guitar-native JS renderer)
- **Chord diagrams** — rendered from chord symbol strings (e.g. "Am", "G7") using ChordJS or similar
- **Playback sync** — Web Audio API reads playback position, highlights current chord block based on timestamps from pipeline output
- **Web architecture** — FastAPI (Python) on Railway handles the pipeline; alphaTab renders in browser. Server stays pure Python.
- **Melody tabs** — deferred. Requires fretboard mapper. Add post-V1 once there's user demand signal.

---

## Primary User (Keep This in Mind When Making Decisions)

**The Music-Curious Non-Musician**
- Uses Suno/Udio to generate songs they genuinely love
- Has never played guitar (or gave up years ago)
- Motivated to learn for the first time because it is their song
- Does not know what a chord progression is
- Does not know what Chordify is
- Will churn fast if the first 15 minutes do not deliver a genuine "I'm doing it" moment
- Does NOT need: transcription accuracy, stems, MIDI editing, complex controls

**Design rule — enforce this always:** If a feature makes a total non-musician feel dumb, it belongs in Phase 2+, not V1.
