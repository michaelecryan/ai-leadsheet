# AI Lead Sheet — Claude Working Document

> **For Claude:** Read this entire file before writing any code. This is the source of truth.
> After reading, confirm: what is built, what is in scope for this session, and what is off-limits.

---

## What This Product Does

Converts AI-generated MIDI files (from Suno, Udio) into clean, guitarist-readable lead sheets.
Output = melody line + chord symbols. NOT a transcription. NOT a notation editor.

**Core principle: "Make it playable, not accurate."**

---

## Tech Stack

- Language: Python
- Package manager: `uv` (not pip, not poetry)
- Music library: `music21`
- Run command: `uv run python -m leadsheet.cli generate song.mid --out chart.xml`
- Output format: MusicXML (`.xml`)
- Entry point: `main.py`
- Key files: `analysis.py`, `export.py`

---

## Current Build State

### ✅ Built and Working
- MIDI parsing (`midi.py`) — tempo, time sig, note extraction
- Key detection (`analysis.py`) — music21 analyzer
- Gesture classifier (`analysis.py`) — melody / dyad / strum classification
- Chord inference by measure (`analysis.py`)
- Chord simplification (`simplify.py`) — extensions, enharmonics, slash chords
- Capo suggestion (`simplify.py`) — frets 1–7, guitar-friendly keys
- MusicXML export (`export.py`) — gesture-aware: notes, dyads, slash noteheads; treble clef forced
- CLI (`cli.py`) — Typer, --simplify/--no-simplify, --inspect, rich console output
- Audio transcription (`audio.py`) — Basic Pitch → temp MIDI → pipeline
- Pitch range filter (`analysis.py`) — strips overtones outside E2–E5 (MIDI 40–76)
- Calibrated against "Idea #1 - Acoustic Alternative.mp3": chord progression correct, thresholds left at defaults

### 🔄 Next Up: Arpeggio Detection
- **Problem:** Fingerpicked guitar notes are sequential, not simultaneous. They land in separate 8th-note grid slots and get classified as scattered melody notes instead of chord arpeggios. This is the primary remaining cause of wonky melody output.
- **Design:** See gesture table below. Runs of consecutive melody-classified notes that form a recognizable chord harmony within ~1–2 beats should collapse into a single `ARPEGGIO` gesture (chord symbol + arpeggio mark).
- **Do not implement without explicit user instruction.**

### ❌ Not Started (Future Phases)
- PDF export (Phase 2)
- Web UI (Phase 3)
- Accounts/payment (Phase 4)
- `--for guitar|piano` CLI flag (Phase 2)
- Chord diagrams (Phase 2)

---

## Audio-First Testing Strategy

Audio input (`audio.py` via Basic Pitch) was added early to enable free testing
with Suno/Udio audio exports, avoiding the Suno Premier paywall for MIDI export.

This is NOT a change in product strategy — MIDI remains the primary V1 input.
Audio input is Phase 3 scope but the code exists and is functional.

**Known tradeoff:** Audio transcription introduces noise (guitar overtones, attack
transients, sympathetic resonance) that MIDI won't have. Expect cleaner output
once tested with real Suno MIDI exports.

**Market implication:** Audio input reaches all Suno/Udio users (free tier).
MIDI input requires users to be on a paid plan. This significantly expands TAM
and is worth validating in Phase 3 messaging.

**Open question:** Does audio input quality meet the playability bar for our
persona, or does it require MIDI for acceptable output? Answer this empirically
before committing to audio as a primary input path.

Do not expand audio.py without explicit instruction.

---

## Current Session Scope

**Before starting any session, the user will specify what we're working on.**
If no scope is given, ask: "What are we working on today?" before touching any code.

Do not expand scope beyond what is stated for the session.

---

## Output Contract — What a Valid Lead Sheet Contains

| Element | Included | Notes |
|---|---|---|
| Melody line | ✅ | Single notes, readable rhythm |
| Chord symbols | ✅ | Above the staff, per measure |
| Key signature | ✅ | Guitar-friendly keys preferred |
| Time signature | ✅ | Detected from MIDI |
| Chord simplification | ✅ | Extensions stripped to playable shapes |
| Full piano voicings | ❌ | Never add |
| Bass line | ❌ | Never add |
| Drum parts | ❌ | Never add |
| Tabs | ❌ | Out of scope for V1 |

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
| Arpeggio | 3–6 notes from same harmony, sequential | Chord symbol + arpeggio mark | ❌ Next |

**Arpeggio detection** is the active next task. Do not implement without user instruction.

---

## Hard Rules — Never Do These

- ❌ Do not add audio/MP3 input support
- ❌ Do not build a web UI or API endpoint
- ❌ Do not add PDF export
- ❌ Do not add accounts, auth, or payment logic
- ❌ Do not add drum, bass, or piano voicing output
- ❌ Do not install new dependencies without asking first
- ❌ Do not rename or restructure files without asking
- ❌ Do not rewrite working modules to "improve" them unless asked

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
1. CLI runs end-to-end on a Suno/Udio MIDI export without errors
2. MusicXML output opens in MuseScore without errors
3. Chord symbols are guitar-playable (no unplayable extensions)
4. Output is demonstrably cleaner than default MuseScore MIDI import
5. Validated on 5–10 real AI-generated MIDI files

---

## Roadmap Reference (Do Not Build Ahead)

| Phase | Focus | Status |
|---|---|---|
| 1 | CLI engine. MIDI in, MusicXML out. Simplification. | 🔄 Active |
| 2 | PDF export. Formatting polish. Capo suggestions. | Not started |
| 3 | Web UI. MIDI upload. Free tier. Audio input via Basic Pitch. | Not started |
| 4 | Soft paywall. ~$10–15/month or per-export pricing. | Not started |

---

## Primary User (Keep This in Mind When Making Decisions)

**The AI-curious guitarist**
- Uses Suno/Udio to generate songs
- Plays guitar (beginner–intermediate)
- Not a music theory expert
- Wants to sit down and play what the AI made
- Values output they can print, read, and play in one session
- Does NOT need: transcription accuracy, stems, MIDI editing, piano voicings
