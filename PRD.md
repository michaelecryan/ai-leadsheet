# AI Lead Sheet — Product Requirements Document

**Version:** 1.1
**Status:** Active
**Last Updated:** 2026-03-04

---

## 1. Problem

AI music tools like Suno and Udio let anyone generate a song. But the output is a black box — you can't sit down and play it.

The current workaround: export audio → MuseScore → manual cleanup. It's slow, produces cluttered notation, and outputs something closer to a full transcription than something you'd hand to a musician.

There is no tool that takes AI-generated audio and produces a clean, guitarist-readable chord chart you can actually play along with.

**The market reality:** Suno/Udio MIDI export requires a paid plan (~$10/month). Audio export is free for all users. Audio is the primary input path — it reaches a significantly larger audience and produces good enough output on synthesized AI audio.

---

## 2. Solution

**AI Lead Sheet** converts AI-generated audio or MIDI into a clean chord chart — then lets you play along with the song, with chords highlighting in sync as the audio plays.

Not a transcription. Not a notation editor. A chord chart: chord symbols per measure, in a guitar-friendly key, with playable chord shapes — and a play-along mode so you always know where you are in the song.

---

## 3. Persona

**Primary User: The AI-curious guitarist**

- Uses Suno or Udio to generate songs
- Plays guitar (beginner to intermediate)
- Wants to actually sit down and play what the AI made
- Frustrated that AI song output is unreadable or unplayable
- Not a music theory expert — needs the tool to handle key detection and chord cleanup
- Values a tool they can use start-to-finish in one session: upload, get chart, play along

**They are not:**
- A session musician needing transcription accuracy
- A producer needing stems or MIDI editing
- A pianist needing full voicings

---

## 4. The Core Product Loop

This is the experience we are building toward. Every decision should serve this loop.

1. **Upload** — user uploads an MP3 or WAV (Suno/Udio export)
2. **Generate** — pipeline processes audio, outputs a chord chart with timestamps
3. **Play along** — user presses play, chords highlight in sync with the audio

Step 3 is the "aha" moment. Steps 1 and 2 are table stakes to get there.

---

## 5. Output Contract

A valid AI Lead Sheet output is:

| Element | Included | Notes |
|---|---|---|
| Chord symbols | ✅ | Primary output — per measure |
| Key signature | ✅ | Guitar-friendly keys preferred |
| Time signature | ✅ | Detected from input |
| Chord simplification | ✅ | Extensions stripped to playable shapes |
| Capo suggestion | ✅ | When key is guitar-unfriendly |
| Chord timestamps | ✅ | Required for playback sync |
| Melody line | 🔄 | Deprioritised — messy from Basic Pitch; may return Phase 2 |
| Full piano voicings | ❌ | Out of scope |
| Bass line | ❌ | Out of scope |
| Drum parts | ❌ | Out of scope |
| Tabs | ❌ | Out of scope for V1 |

---

## 6. Core Differentiator

**"Make it playable" — not "make it accurate."**

MuseScore optimizes for transcription fidelity. AI Lead Sheet optimizes for playability and play-along experience.

Two wedges:

**Simplification layer** — what a human musician would do when arranging a chart, automated:
- Strip chord extensions beyond 7th (Cmaj9 → Cmaj7, Gmaj13 → G)
- Normalize enharmonics to guitar-friendly spellings (Gb → F#)
- Prefer guitar-native keys (E, A, G, D, C, Em, Am)
- Suggest capo position if key is guitar-unfriendly

**Playback sync** — nobody else has this for AI-generated audio specifically:
- Chords highlight in real time as the song plays
- Karaoke-style — you always know where you are
- Designed for guitarists who want to jam, not read notation

---

## 7. Competitive Landscape

| Tool | What they do | Gap |
|---|---|---|
| MuseScore | Full transcription from MIDI | Not optimised for playability or guitar; no audio-in workflow |
| Ultimate Guitar | Pre-made tabs and chords | No audio processing; human-uploaded only |
| Moises | Stem separation and playback | Not chart-focused; no chord chart output |
| Chordify | Chord detection from audio | No guitar optimisation; no play-along sync; generic UI |

AI Lead Sheet is the only tool targeting the specific workflow: AI-generated audio → guitarist-readable chord chart → play along in sync.

---

## 8. V1 Feature Set

### Must Have
- [x] Parse audio file via Basic Pitch transcription (primary input path)
- [x] Parse MIDI file (secondary input path — cleaner output, smaller audience)
- [x] Detect key signature
- [x] Gesture classification — melody, dyad, strum, arpeggio
- [x] Infer chord symbols grouped by measure
- [x] Apply simplification rules (extensions, enharmonics, capo suggestions)
- [x] CLI interface with `--simplify`, `--inspect` flags
- [ ] Web UI — upload audio, receive chord chart in browser
- [ ] Audio playback in browser with real-time chord highlighting
- [ ] Chord timestamps in pipeline output (to drive sync)

### Should Have
- [x] Capo suggestions for guitar-unfriendly keys
- [x] `--inspect` flag for calibration visibility
- [ ] Saved charts (basic, pre-auth)
- [ ] Validation across 5–10 Suno/Udio audio exports (in progress)

### Won't Have in V1
- PDF export (Phase 2)
- Chord diagrams (Phase 2)
- Accounts or payment (Phase 3)
- Advanced reharmonization
- Tab notation (Phase 4)
- Collaboration features

---

## 9. Simplification Rules (V1)

| Rule | Example | Output |
|---|---|---|
| Strip extensions beyond 7 | Cmaj9 | Cmaj7 |
| Strip color tones | G13#11 | G7 |
| Normalize enharmonics | Gb major | F# major |
| Prefer open guitar keys | Bb major | Suggest capo 1, A shapes |
| Reduce slash chords | C/E | C |

---

## 10. Success Criteria

V1 is successful when:

1. User can upload an audio file via web UI and receive a chord chart
2. Chord chart is accurate enough to play along with the original song
3. Audio plays back in browser with chords highlighting in sync
4. Chord symbols are guitar-playable (no unplayable extensions)
5. Output is cleaner and faster to use than default MuseScore MIDI import
6. Validated on 5–10 real Suno/Udio audio exports across different genres
7. Demo video posted to r/SunoAI and r/Guitar — generates genuine interest

---

## 11. Phase Roadmap

### Phase 1 — CLI Engine ✅ Done
CLI pipeline. Audio or MIDI in, MusicXML out. Simplification, gesture classification, arpeggio detection. Validated on Suno audio exports.

### Phase 2 — Web UI Shell 🔄 Active
FastAPI backend. Upload endpoint. Chord chart rendered in browser (alphaTab). Basic frontend. Deployed to public URL (Railway or Render).

### Phase 3 — Playback Sync 🔄 Active
Audio playback in browser. Chord timestamps from pipeline. Real-time chord highlighting. Demo video. Community launch.

### Phase 4 — Chord Quality
Essentia and Demucs pipeline evaluation in separate branch. Merge best approach. Target: chart accurate enough that a guitarist can follow without second-guessing.

### Phase 5 — User Accounts + Storage
Auth (Clerk or Supabase). Saved charts. Upload history. Dashboard. Prerequisite for charging money.

### Phase 6 — Monetisation
Stripe integration. Free tier (3 uploads/month). Paid tier ($5–10/month, unlimited). Pricing page. Tier enforcement.

### Phase 7 — Output Polish
Chord diagrams (ChordJS). PDF/printable export. Formatting improvements.

### Phase 8 — Melody Tabs
Fretboard mapper (pitch → string + fret). Only if user demand signals it post-launch.

---

## 12. Open Questions

1. ~~Do AI music creators want printable charts or just playback?~~ **Answered: playback sync is the core feature. Charts are the means, play-along is the end.**
2. What is the minimum chord accuracy required for the play-along to feel useful?
3. Is $5/month or $10/month the right price point for this audience?
4. ~~Is MIDI-first sufficient, or does audio input need to come earlier?~~ **Answered: audio is primary.**

---

## 13. Gesture-Aware Notation

| Gesture | Signal | Notation | Status |
|---|---|---|---|
| Single-note line | 1 note per grid slot | Notes on staff | ✅ Done |
| Dyad / power chord | 2 simultaneous notes | Interval notation | ✅ Done |
| Chord strum | 3+ simultaneous notes | Chord symbol + slash notehead | ✅ Done |
| Arpeggio | 3–6 sequential notes forming a chord | Chord symbol + arpeggio mark | ✅ Done |

**Known audio limitation:** Chord-melody style playing causes melody notes to bleed into strum clusters. This is a Basic Pitch limitation for live acoustic recordings. Suno/Udio synthesized audio handles significantly better.

---

## 14. Out of Scope (Permanent)

- Real-time collaboration
- DAW plugin
- Full arrangement / multi-instrument scores
- AI reharmonization or style transfer
- Piano or non-guitar optimised output

---

*This document is the source of truth for V1 scope. Any feature not listed under V1 must go through a scope change discussion before being added.*