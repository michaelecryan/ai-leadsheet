# ai-leadsheet

> Your AI song as your first music lesson.

## What it is

ai-leadsheet is for people who make songs with Suno or Udio — and for the first time in their life, want to understand and play what they've created.

You don't need to play guitar. You don't need to know what a chord is. You just need a song you made and a desire to play it.

Upload your Suno or Udio track. The app detects the key (and explains what that means), shows you the 3–5 chords in your song as big, simple finger diagrams, and lets you play along as chords highlight in sync with the audio. Then it points you to the exact JustinGuitar or Marty Music lesson that teaches those chords or relevant concepts depending on your level of understanding.

Most songs — even complex-sounding ones — are just 4 chords. ai-leadsheet shows you that. **Your song in 4 chords** is the moment everything clicks.

## Who it's for

- People who use Suno or Udio and want to learn to play their songs on guitar
- Complete beginners — no musical knowledge needed
- Anyone who's generated a song and thought "I wonder if I could actually play this"

## The core loop

1. **Upload** an audio file (MP3 or WAV from Suno/Udio)
2. **Generate** — chord chart produced automatically, guitar-optimised
3. **Play along** — chords highlight in sync with audio playback

## What makes it different

Most tools are built for people who already play. This tool is built for the moment *before* that — when you've just made something with AI and you're wondering if you could actually learn to play it.

That means:
- Plain English explanations — no assumed music knowledge
- Large, simple chord diagrams — not notation, not tabs, just where to put your fingers
- Chords simplified to what's actually playable (Cmaj9 → Cmaj7, Gb → F#)
- Capo suggestions when the key doesn't sit well on a fretboard
- Contextual lesson links — the exact JustinGuitar or Marty Music video for your chords
- Play-along sync — follow the chords in real time as your song plays

## Tech stack

**Current pipeline:**
- **Audio processing:** Basic Pitch (Spotify) — pitch/MIDI extraction from audio
- **Music analysis:** music21 — key detection, gesture classification, chord inference
- **Chord simplification:** custom rules engine
- **Backend:** Python (FastAPI — in progress)
- **Frontend:** Web UI (in progress — currently CLI only)
- **Deployment:** Railway (planned)

**Proposed pipeline (under evaluation in separate branch):**

Demucs (Meta) → Basic Pitch → Essentia chord detection → chart renderer

- **Demucs** — source separation (vocals / bass / drums / other). Cleaner stems = cleaner transcription input.
- **Basic Pitch** — pitch/MIDI extraction, run on isolated stems rather than full mix
- **Essentia** — chord detection and melody extraction (`PredominantPitchMelodia`), more targeted than Basic Pitch for dominant melodic line

## Current status

Phase 1 (CLI engine) is complete and working:

```bash
uv run python -m leadsheet.cli generate song.mid --out chart.xml
```

Phase 2 (web UI), Phase 3 (playback sync), and Phase 3b (education layer — contextual JustinGuitar / Marty Music lessons) are in active development.

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| 1 | CLI engine — audio/MIDI in, chord chart out | ✅ Done |
| 2 | Web UI — upload in browser, chart rendered in browser | 🔄 In progress |
| 3 | Playback sync — chords highlight in real time | 🔄 In progress |
| 4 | Chord quality improvements | Planned |
| 5 | User accounts + saved charts | Planned |
| 6 | Paid tier (~$5–10/month) | Planned |

## Positioning

| Tool | Who it's for |
|---|---|
| Chordify | People who already play guitar |
| Moises | Practicing musicians and producers |
| Ultimate Guitar | Guitarists learning existing songs |
| Chord AI | Guitarists learning from any audio |
| **ai-leadsheet** | **Music-curious non-musicians with an AI song** |

The gap nobody owns: *your AI song as your first structured music lesson.* That's what this is.
