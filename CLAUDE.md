# AI Lead Sheet — Claude Working Document

> **For Claude:** Read this entire file before writing any code. This is the source of truth.
> After reading, confirm: what is built, what is in scope for this session, and what is off-limits.

> **End of every session:** Ask Claude Code to update the Current Build State section to reflect what was built. Keep this file current — it is the memory of the project.

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
- Backend: FastAPI
- Output format: JSON (chord chart) → browser renderer
- Legacy output: MusicXML (`.xml`) via CLI still supported
- Entry point: `main.py`
- Key files: `analysis.py`, `export.py`, `audio.py`, `simplify.py`, `cli.py`
- Deployment target: Railway

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
- FastAPI backend (`main.py`) — `/health` and `/upload` endpoints, accepts audio/MIDI, returns chord chart JSON
- Web UI (`frontend/index.html`) — drag-and-drop upload, loading state with time expectation copy, key + capo + scales display
- "Your song in X chords" hero section — top 6 chords by frequency with pure SVG finger diagrams (~30 chord shapes in `CHORD_SHAPES` lookup)
- SVG chord diagram renderer (`buildChordSvg()` in `frontend/index.html`) — no external library; handles open strings, muted strings, barre chords
- Bar-by-bar chord grid — full progression below hero section
- Chord timestamps in pipeline output (`time_seconds` per chord, wired up ready for playback sync)
- Railway deployment config — `Procfile` + `railway.toml` committed; app binds to `0.0.0.0:$PORT`, healthcheck at `/health`
- Railway deployed and live at `ai-leadsheet-production.up.railway.app` — requires `NIXPACKS_PYTHON_VERSION=3.11` env var in Railway dashboard
- ONNX runtime backend (`onnxruntime`) — replaces TFLite for cross-platform Basic Pitch inference on Railway (Linux x86_64)
- Python 3.11 (upgraded from 3.9 for onnxruntime compatibility)
- Diminished chord simplification (`simplify.py`) — `dim` → minor, `dim7` → `m7`
- YouTube URL ingestion (`/upload-url`) — yt-dlp downloads audio server-side; IFrame Player API syncs chords in browser
- Education layer — static `LESSON_LOOKUP` table (20 chords → JustinGuitar + Marty Music); `renderLessons()` in `frontend/index.html`
- librosa chromagram chord detector (`leadsheet/chord_detector.py`) — default audio path; Basic Pitch fallback via `CHORD_DETECTOR=basic_pitch` env var
- Feature flag `FEATURES.youtubeUrl` in `frontend/index.html` — set `false` for V1 launch (YouTube tab hidden); flip to `true` to re-enable
- Above-the-fold layout — SVG diagrams + chord cards sized to fit with audio player at 1280×800 without scrolling
- Email capture modal — 3s delay after results render; `POST /api/subscribe` → Brevo API (env var `BREVO_API_KEY`); once-per-device via localStorage
- Rate limiting — `slowapi` 10 req/hour per IP on `/upload`; returns 429 with user-friendly message
- Upload hardening — 20MB size limit (HTTP 413); MIME type validation via `filetype` magic bytes (HTTP 415)

### 🔄 Active Development
- Chord output quality improvements (Essentia and Demucs evaluation in separate branch — Phase 4)

### ❌ Not Started (Future Phases)
- PDF export (Phase 7)
- Accounts/auth (Phase 5)
- Payment/paywall (Phase 6)
- `--for guitar|piano` CLI flag (future phase — guitar only for V1)
- Melody tabs / fretboard mapper (Phase 8)
- Piano voicings / piano chord diagrams (later phase — guitar is V1 instrument)
- URL paste input for mobile (desktop-first for V1, mobile capture layer later)

---

## Known Issues

- **Processing speed:** Basic Pitch takes 20–30 seconds for a full track. Workaround under evaluation: process first 60 seconds for fast initial result, full track in background.
- **Progress indicator:** ~~No loading state.~~ Resolved in Issue #6 — loading copy now reads "Transcribing your track… This usually takes 20–40 seconds. Hold tight."
- **Chord chart noise:** ~~Full bar-by-bar chart is overwhelming.~~ Resolved in Issue #6 — hero section now shows top 6 chords by frequency; bar chart is secondary.
- **Diminished chords:** ~~F#dim, Adim, Bdim appearing in output.~~ Resolved — `simplify.py` now collapses `dim` → minor, `dim7` → `m7`.

---

## Input Strategy — Audio is Primary

**Audio is the primary V1 input path.** MIDI is supported and produces cleaner output, but requires a paid Suno plan (Pro ~$10/month). Audio export is available to all free-tier users — a significantly larger audience.

**Hero flow:** Suno/Udio free user exports MP3 → uploads to web UI → gets key + chord diagrams → presses play → follows chords in sync → gets pointed to JustinGuitar lesson.

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
| Chord timestamps | ✅ | Required for playback sync |
| Chord diagrams | ✅ | Core to V1 — large, simple finger diagrams for non-musicians. Rendered from chord symbols. |
| Melody line | 🔄 | Deprioritised — messy from Basic Pitch; may return in Phase 2 |
| Full piano voicings | ❌ | Not in V1 — piano expansion planned for later phase |
| Bass line | ❌ | Never add |
| Drum parts | ❌ | Never add |
| Melody tabs | Phase 8 | Requires fretboard mapper — only if demand signals it |

---

## Simplification Rules (Always Apply Unless `--no-simplify`)

| Rule | Input Example | Output |
|---|---|---|
| Strip extensions beyond 7th | Cmaj9 | Cmaj7 |
| Strip color tones | G13#11 | G7 |
| Normalize enharmonics | Gb major | F# major |
| Prefer guitar-friendly keys | Bb major | Suggest capo 1, A shapes |
| Reduce slash chords | C/E | C |
| Collapse diminished chords | F#dim | F# or nearest playable neighbour |

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

## Architectural Decisions (Resolved)

### Platform: Desktop-First for V1
**Decision:** Desktop-first web app for V1. Mobile is a capture layer only.

**Rationale:** The core learning moment — guitar in hand, following chord sync — happens on desktop with a big screen. Mobile is where discovery happens (user generates a Suno track, wants to save it for later).

**V1 implementation:**
- Desktop: full experience — file upload, chord diagrams, play-along sync, lesson links
- Mobile: URL paste input only — user pastes their Suno/Udio share link or YouTube URL, chart is saved and waiting on desktop. No full feature parity required in V1.

**File upload vs URL input:**
- Desktop: file upload (MP3/WAV drag and drop) — natural workflow
- Mobile: URL paste (Suno share link, Udio link, YouTube URL) — avoids awkward mobile file upload

---

### Education Layer: Curated Lookup Table (Not Live API)
**Decision:** Build a static chord-to-lesson lookup table for V1. No live YouTube API calls yet.

**Rationale:** Faster to build, more reliable, editorial control over quality. Scale to live API later when lesson library needs to grow.

**V1 implementation:**
- Curate the 20 most common beginner chords: Am, G, C, D, E, Em, F, A, Bm, Dm, E7, A7, D7, G7, Cadd9, Dsus2, Esus4, Fmaj7, Cmaj7, B7
- For each chord: best JustinGuitar video + best Marty Music video
- Detected chords → lookup → surface 2–3 relevant videos in UI
- YouTube embeds via YouTube Data API (read-only, API key only — no OAuth required)

**Why no OAuth for YouTube:**
- Surfacing lesson videos = read-only YouTube Data API = API key only, no user login needed
- OAuth only needed if writing to user's account — not required
- Suno/Udio are closed ecosystems with no public API — URL paste is the only integration path

**Future:** Swap static lookup for live YouTube API search once chord coverage needs to scale beyond the 20 core chords.

---

## Hard Rules — Never Do These

- ❌ Do not add drum or bass output
- ❌ Do not add piano voicings or piano chord diagrams until explicitly instructed (planned for later phase, not V1)
- ❌ Do not add accounts, auth, or payment logic until Phase 5
- ❌ Do not add PDF export until Phase 7
- ❌ Do not install new dependencies without asking first
- ❌ Do not rename or restructure files without asking
- ❌ Do not rewrite working modules to "improve" them unless asked
- ❌ Do not expand audio.py without explicit instruction
- ❌ Do not add features that expose complexity to non-musicians — if it would confuse a first-time user, it belongs in Phase 2+

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
| 2 | Web UI shell. FastAPI backend. Upload → key + chords displayed in browser. Large chord diagrams, plain-English key explanation. | ✅ Done |
| 3 | Playback sync. Chords highlight in real time during audio playback. | 🔄 Active |
| 3b | Education layer. Surface contextual JustinGuitar / Marty Music YouTube lessons based on detected chords. Retention mechanism — do not defer past Phase 3. | 🔄 Active |
| 4 | Chord quality improvements. Essentia/Demucs pipeline evaluation. | 🔄 Active |
| 5 | User accounts + chart storage. Auth. Saved charts dashboard. | Not started |
| 6 | Monetisation. Stripe. Free/paid tier. ~$5–10/month. | Not started |
| 7 | PDF export. Formatting polish. | Not started |
| 8 | Melody tabs (fretboard mapper). Post-validation only. | Not started |

---

## Phase 3 Rendering Stack (Decided, Partially Built)

- **Chord chart** — rendered in browser from JSON output (bar-by-bar chord symbols) ✅
- **Key display** — plain-English explanation + capo tip rendering ✅
- **Chord diagrams** — pure SVG renderer built in `frontend/index.html`; `CHORD_SHAPES` lookup + `buildChordSvg()` ✅
- **Hero section** — "Your song in X chords" with top chords by frequency ✅
- **Playback sync** — Web Audio API reads playback position, highlights current chord block based on `time_seconds` timestamps — next to build (Phase 3)
- **Web architecture** — FastAPI (Python) on Railway handles the pipeline; browser renders display. Server stays pure Python. ✅
- **Melody tabs** — deferred. Requires fretboard mapper. Add post-V1 only if user demand signals it.

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