# AI Lead Sheet — Claude Working Document

> **For Claude:** Read this entire file before writing any code. This is the source of truth.
> After reading, confirm: what is built, what is in scope for this session, and what is off-limits.

---

## What This Product Does

Converts AI-generated audio or MIDI files (from Suno, Udio) into clean, guitarist-readable lead sheets — then lets the user play along with the song in sync.

Output = chord chart with real-time highlighting during audio playback. NOT a transcription. NOT a notation editor.

**Core principle: "Make it playable, not accurate."**

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
- PDF export (Phase 2)
- Accounts/auth (Phase 4)
- Payment/paywall (Phase 4)
- `--for guitar|piano` CLI flag (Phase 2)
- Chord diagrams (Phase 2)
- Melody tabs / fretboard mapper (Phase 4)

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

1. **Upload** — user uploads an audio file (MP3/WAV)
2. **Generate** — pipeline processes audio, outputs chord chart with timestamps
3. **Play along** — user presses play, chords highlight in sync with audio playback

Step 3 is the "aha" moment. Everything else is table stakes to get there.

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
| Full piano voicings | ❌ | Never add |
| Bass line | ❌ | Never add |
| Drum parts | ❌ | Never add |
| Chord diagrams | Phase 2 | Rendered from chord symbols |
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

- ❌ Do not add drum, bass, or piano voicing output
- ❌ Do not add accounts, auth, or payment logic until Phase 4
- ❌ Do not add PDF export until Phase 2
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

V1 is complete when ALL of these are true:
1. User can upload an audio file via web UI and receive a chord chart
2. Chord chart is accurate enough to play along with the song
3. Audio plays back in browser with chords highlighting in sync
4. Chord symbols are guitar-playable (no unplayable extensions)
5. Validated on 5–10 real Suno/Udio audio exports across different genres
6. Demo video recorded and posted to r/SunoAI and r/Guitar for feedback

---

## Roadmap Reference (Do Not Build Ahead)

| Phase | Focus | Status |
|---|---|---|
| 1 | CLI engine. Audio/MIDI in, MusicXML out. Simplification. Arpeggio detection. | ✅ Done |
| 2 | Web UI shell. FastAPI backend. Upload → chord chart in browser. | 🔄 Active |
| 3 | Playback sync. Chords highlight in real time during audio playback. | 🔄 Active |
| 4 | Chord quality improvements. Essentia/Demucs pipeline evaluation. | 🔄 Active |
| 5 | User accounts + chart storage. Auth. Saved charts dashboard. | Not started |
| 6 | Monetisation. Stripe. Free/paid tier. ~$5–10/month. | Not started |
| 7 | Chord diagrams. PDF export. Formatting polish. | Not started |
| 8 | Melody tabs (fretboard mapper). Post-validation only. | Not started |

## Phase 2/3 Rendering Stack (Decided, Not Yet Built)

- **Standard notation / chord chart** — rendered client-side from MusicXML using **alphaTab** (guitar-native JS renderer)
- **Chord diagrams** — rendered from chord symbol strings (e.g. "Am", "G7") using ChordJS or similar
- **Playback sync** — Web Audio API reads playback position, highlights current chord block based on timestamps from pipeline output
- **Web architecture** — FastAPI (Python) on Railway handles the pipeline; alphaTab renders in browser. Server stays pure Python.
- **Melody tabs** — deferred. Requires fretboard mapper. Add post-V1 once there's user demand signal.

---

## Primary User (Keep This in Mind When Making Decisions)

**The AI-curious guitarist**
- Uses Suno/Udio to generate songs
- Plays guitar (beginner–intermediate)
- Not a music theory expert
- Wants to sit down and play what the AI made
- Values a tool they can use in one session — upload, get chart, play along
- Does NOT need: transcription accuracy, stems, MIDI editing, piano voicings
