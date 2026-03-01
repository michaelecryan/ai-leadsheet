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

## Input Strategy — Audio is Primary

**Audio is the primary V1 input path.** MIDI is supported and produces cleaner output,
but requires a paid Suno plan (Pro ~$10/month). Audio export is available to all free-tier
users — a significantly larger audience.

**Hero flow:** Suno/Udio free user exports MP3 → uploads → gets a playable lead sheet.

**Audio quality findings (from testing):**
- Suno/Udio synthesized audio transcribes well — chord progressions correct, gestures clean
- Live acoustic guitar recordings are harder: overtones, tuning variance, and chord-melody
  bleed (picked melody notes absorbed into chord clusters) degrade output quality
- These issues are specific to live recordings, not the primary use case

**MIDI as premium path:** Supports users on paid Suno plans who want cleaner output.
Worth keeping, but not the lead product story.

**Future audio improvement (not yet built):** Top-note extraction — when a strum cluster
contains many notes, the highest pitch is often a melody note that was picked rather than
strummed. Separating it would improve chord-melody style audio. Defer until validated needed.

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
| Chord diagrams | ✅ Phase 2 | Rendered from chord symbols (e.g. "Am") — not from audio |
| Melody tabs | 🔄 Phase 3+ | Requires fretboard mapper; defer until web UI exists |

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
1. CLI runs end-to-end on a Suno/Udio audio export without errors
2. MusicXML output opens in MuseScore/Flat.io without errors
3. Chord symbols are guitar-playable (no unplayable extensions)
4. Output is demonstrably cleaner than default MuseScore MIDI import
5. Validated on 5–10 real Suno/Udio audio exports across different genres

---

## Roadmap Reference (Do Not Build Ahead)

| Phase | Focus | Status |
|---|---|---|
| 1 | CLI engine. MIDI in, MusicXML out. Simplification. Arpeggio detection. | 🔄 Active |
| 2 | Chord diagrams. Lead sheet PDF delivery. Formatting polish. | Not started |
| 3 | Web UI (FastAPI + Railway). Audio upload. alphaTab rendering client-side. | Not started |
| 4 | Melody tabs (fretboard mapper). Soft paywall. ~$10–15/month. | Not started |

## Phase 2/3 Rendering Stack (Decided, Not Yet Built)

**Goal:** Deliver a printable lead sheet to the user — not a MusicXML file they have to open elsewhere.

- **Chord diagrams** — rendered from chord symbol strings (e.g. "Am", "G7") using a JS library (ChordJS or similar). Tractable from what we already produce. Priority item for Phase 2.
- **Standard notation** — rendered client-side from MusicXML using **alphaTab** (guitar-native JS renderer). alphaTab is preferred over Verovio because it understands guitar-specific notation natively.
- **Melody tabs** — deferred. Requires a fretboard mapper (pitch → string + fret), which is a non-trivial problem. Add post-V1 once there's user demand signal.
- **Web architecture** — FastAPI (Python) on Railway handles the pipeline; alphaTab renders everything in the browser. Server stays pure Python, no notation rendering server-side.

---

## Primary User (Keep This in Mind When Making Decisions)

**The AI-curious guitarist**
- Uses Suno/Udio to generate songs
- Plays guitar (beginner–intermediate)
- Not a music theory expert
- Wants to sit down and play what the AI made
- Values output they can print, read, and play in one session
- Does NOT need: transcription accuracy, stems, MIDI editing, piano voicings
