# ai-leadsheet

> Upload an AI-generated song. Get a chord chart. Play along.

## What it is

ai-leadsheet is a tool for musicians who generate music with Suno or Udio and want to actually *play* what they've made.

Upload an audio file. The app processes it and generates a chord chart in a guitar-friendly key, with simplified, playable chord shapes. Press play and follow the chords in sync as the song plays back — like a karaoke scroll for guitarists.

No more guessing the key or chord chart. No more cleaning up MuseScore output. Just upload, generate, and play.

## Who it's for

- Guitarists using AI music tools (Suno, Udio) who want to play their generated songs fast
- Beginner to intermediate players who don't want to transcribe by ear
- Anyone who's generated a song and hit the wall of "now what?"

## The core loop

1. **Upload** an audio file (MP3 or WAV from Suno/Udio)
2. **Generate** — chord chart produced automatically, guitar-optimised
3. **Play along** — chords highlight in sync with audio playback

## What makes it different

Most tools optimise for transcription accuracy. This tool optimises for **playability**.

That means:
- Chord extensions stripped to guitar-playable shapes (Cmaj9 → Cmaj7)
- Enharmonics normalised to guitar-friendly spellings (Gb → F#)
- Capo suggestions when the key doesn't sit well on a fretboard
- Chord chart output, not full notation — what a musician actually needs

## Tech stack

- **Audio processing:** Basic Pitch (Spotify) for pitch/MIDI extraction
- **Music analysis:** music21 — key detection, gesture classification, chord inference
- **Chord simplification:** custom rules engine
- **Backend:** Python (FastAPI — in progress)
- **Frontend:** Web UI (in progress — currently CLI only)
- **Deployment:** Railway (planned)

## Current status

Phase 1 (CLI engine) is complete and working:

```bash
uv run python -m leadsheet.cli generate song.mid --out chart.xml
```

Phase 2 (web UI) and Phase 3 (playback sync) are in active development.

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

Sits in the gap between:

- **MuseScore** — full transcription, not optimised for playability or guitar
- **Ultimate Guitar** — human-uploaded tabs, no audio processing
- **Moises** — stem separation and playback, not chart-focused
- **Chordify** — chord detection but no guitar optimisation or play-along sync

ai-leadsheet is built specifically for the AI-generated audio → guitarist workflow that nobody else has targeted.
