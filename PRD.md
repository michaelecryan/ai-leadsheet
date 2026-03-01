# AI Lead Sheet — Product Requirements Document

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-03-01

---

## 1. Problem

AI music tools like Suno and Udio let anyone generate a song. But the output is a black box — you can't sit down and play it.

The current workaround: export audio (or MIDI if you're on a paid plan) → MuseScore → manual cleanup. It's slow, produces cluttered notation, and outputs something closer to a transcription than something you'd hand to a musician.

There is no tool that takes AI-generated audio or MIDI and produces a clean, guitarist-readable lead sheet.

**The market reality:** Suno/Udio MIDI export requires a paid plan (Suno Pro ~$10/month). Audio export is available to all free-tier users. Audio is therefore the primary input path — it reaches a significantly larger audience.

---

## 2. Solution

**AI Lead Sheet** converts AI-generated audio or MIDI into clean, human-playable lead sheets — optimized for guitar.

Not a transcription. Not a notation editor. A lead sheet: melody line + chord symbols, in a readable key, with guitar-playable chords.

---

## 3. Persona

**Primary User: The AI-curious guitarist**

- Uses Suno or Udio to generate songs
- Plays guitar (beginner to intermediate)
- Wants to actually sit down and play what the AI made
- Frustrated that AI song output is unreadable or unplayable
- Not a music theory expert — needs the tool to handle key detection and chord cleanup
- Values output they can print, read, and play in one session

**They are not:**
- A session musician needing transcription accuracy
- A producer needing stems or MIDI editing
- A pianist needing full voicings

---

## 4. Output Contract

A valid AI Lead Sheet output is:

| Element | Included | Notes |
|---|---|---|
| Melody line | ✅ | Single notes, readable rhythm |
| Chord symbols | ✅ | Above the staff, per measure |
| Key signature | ✅ | Guitar-friendly keys preferred |
| Time signature | ✅ | Detected from input |
| Chord simplification | ✅ | Extensions stripped to playable shapes |
| Full piano voicings | ❌ | Out of scope |
| Bass line | ❌ | Out of scope |
| Drum parts | ❌ | Out of scope |
| Tabs | ❌ | Out of scope for V1 |

---

## 5. Core Differentiator

**"Make it playable" — not "make it accurate."**

MuseScore optimizes for transcription fidelity. AI Lead Sheet optimizes for playability.

The simplification layer is the wedge:

- Strip chord extensions beyond 7th (Cmaj9 → Cmaj7, Gmaj13 → G)
- Normalize enharmonics to guitar-friendly spellings (Gb → F#)
- Prefer guitar-native keys (E, A, G, D, C, Em, Am)
- Flag or suggest capo position if key is guitar-unfriendly

This is what a human musician would do when arranging a chart. The tool does it automatically.

---

## 6. V1 Feature Set

### Must Have
- [x] Parse audio file via Basic Pitch transcription (primary input path)
- [x] Parse MIDI file (secondary input path — cleaner output, smaller audience)
- [x] Detect key signature
- [x] Gesture classification — melody, dyad, strum, arpeggio
- [x] Infer chord symbols grouped by measure
- [x] Apply simplification rules (extensions, enharmonics)
- [x] Export clean MusicXML (openable in MuseScore / Flat.io / other notation apps)
- [x] CLI interface with `--simplify`, `--inspect` flags

### Should Have
- [x] Capo suggestions for guitar-unfriendly keys
- [x] `--inspect` flag for calibration visibility
- [ ] Validation across 5–10 Suno/Udio audio exports (in progress)

### Won't Have in V1
- Web UI (Phase 3)
- PDF export (Phase 2)
- Chord diagrams (Phase 2)
- Accounts or payment
- Advanced reharmonization
- Tab notation
- Collaboration features

---

## 7. CLI Interface (V1)

```bash
# Basic usage
uv run python -m leadsheet.cli generate song.mid --out chart.xml

# With simplification disabled
uv run python -m leadsheet.cli generate song.mid --out chart.xml --no-simplify

# Output example
Loading MIDI: song.mid
Detected Key: E major
Chord progression: E | A | B | C#m
Exported: chart.xml
```

---

## 8. Simplification Rules (V1)

| Rule | Example | Output |
|---|---|---|
| Strip extensions beyond 7 | Cmaj9 | Cmaj7 |
| Strip color tones | G13#11 | G7 |
| Normalize enharmonics | Gb major | F# major |
| Prefer open guitar keys | Bb major | Suggest capo 1, A shapes |
| Reduce slash chords | C/E | C |

---

## 9. Success Criteria

V1 is successful when:

1. CLI runs end-to-end on a Suno/Udio MIDI export
2. MusicXML output opens in MuseScore without errors
3. Chord symbols are guitar-playable (no unplayable extensions)
4. Output is cleaner and faster to use than default MuseScore MIDI import
5. Validated on 5–10 real AI-generated MIDI files

---

## 10. Phase Roadmap

### Phase 1 — Engine (Now)
CLI pipeline. Audio or MIDI in, MusicXML out. Simplification, gesture classification, arpeggio detection baked in. Validate output quality across Suno/Udio songs before moving on.

### Phase 2 — Output Quality
Chord diagrams rendered from chord symbols. Lead sheet PDF/printable delivery (alphaTab client-side rendering). Formatting polish.

### Phase 3 — Web Product
Minimal web UI (FastAPI + Railway). Upload MP3/audio, download lead sheet. Free tier with export limit. Hero flow: Suno free-tier user uploads audio → gets playable chart. Launch to AI music communities (Reddit, Discord).

### Phase 4 — Monetization + Tabs
Soft paywall. ~$10–15/month or per-export pricing. Melody tab generation (fretboard mapper) if user demand signals it. MIDI input as premium path for cleaner output.

---

## 11. Open Questions

1. Do AI music creators actually want printable charts, or just playback?
2. Is simplification more valuable than transcription accuracy to this user?
3. What is the minimum output quality required to feel superior to MuseScore import?
4. ~~Is MIDI-first sufficient, or does audio input need to come earlier than expected?~~ **Answered: audio is primary.** MIDI requires a paid Suno plan; audio reaches all free-tier users. Audio quality on Suno/Udio output (synthesized) is meaningfully better than live instrument recording.

---

## 13. Gesture-Aware Notation (Done)

Replaced single-note melody extraction with a full gesture classifier:

| Gesture | Signal | Notation | Status |
|---|---|---|---|
| Single-note line | 1 note per grid slot | Notes on staff | ✅ Done |
| Dyad / power chord | 2 simultaneous notes | Interval notation | ✅ Done |
| Chord strum | 3+ simultaneous notes | Chord symbol + slash notehead | ✅ Done |
| Arpeggio | 3–6 sequential notes forming a chord | Chord symbol + slash notehead | ✅ Done |

**Known audio limitation:** Chord-melody style playing (picked melody over ringing chord) causes melody notes to bleed into strum clusters. This is a Basic Pitch limitation for live acoustic recordings; Suno/Udio synthesized audio handles significantly better. Top-note extraction is a possible future improvement for audio quality.

---

## 12. Out of Scope (Permanent or Long-Term)

- Audio transcription — **built and functional** in V1. Primary input path.
- Real-time collaboration
- DAW plugin
- Full arrangement / multi-instrument scores
- AI reharmonization or style transfer

---

*This document is the source of truth for V1 scope. Any feature not listed under V1 must go through a scope change discussion before being added.*
