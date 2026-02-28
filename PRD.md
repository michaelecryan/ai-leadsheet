# AI Lead Sheet — Product Requirements Document

**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2026-02-28

---

## 1. Problem

AI music tools like Suno and Udio let anyone generate a song. But the output is a black box — you can export MIDI, but you can't sit down and play it.

The current workaround: MIDI → MuseScore → manual cleanup. It's slow, produces cluttered notation, and outputs something closer to a transcription than something you'd hand to a musician.

There is no tool that takes AI-generated MIDI and produces a clean, guitarist-readable lead sheet.

---

## 2. Solution

**AI Lead Sheet** converts AI-generated MIDI into clean, human-playable lead sheets — optimized for guitar.

Not a transcription. Not a notation editor. A lead sheet: melody line + chord symbols, in a readable key, with guitar-playable chords.

---

## 3. Persona

**Primary User: The AI-curious guitarist**

- Uses Suno or Udio to generate songs
- Plays guitar (beginner to intermediate)
- Wants to actually sit down and play what the AI made
- Frustrated that MIDI exports are unreadable or unplayable
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
| Time signature | ✅ | Detected from MIDI |
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
- [ ] Parse MIDI file (local input)
- [ ] Detect key signature
- [ ] Extract melody line
- [ ] Infer chord symbols grouped by measure
- [ ] Apply simplification rules (extensions, enharmonics)
- [ ] Export clean MusicXML (openable in MuseScore / other notation apps)
- [ ] CLI interface

### Should Have
- [ ] `--simplify` flag (on by default, can disable for raw output)
- [ ] Print detected key to terminal
- [ ] Print chord progression summary to terminal

### Won't Have in V1
- Audio / MP3 input
- Web UI
- PDF export (Phase 2)
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
CLI pipeline. MIDI in, MusicXML out. Simplification baked in.

### Phase 2 — Output Quality
PDF export. Formatting polish. Capo suggestions. Chord diagram option.

### Phase 3 — Product Experiment
Minimal web UI. Upload MIDI, download lead sheet. Free tier with export limit. Launch to AI music communities (Reddit, Discord). Accept MP3/WAV via Basic Pitch transcription layer feeding existing MIDI pipeline. Unlocks users who can't or won't export MIDI.

### Phase 4 — Monetization
Soft paywall. ~$10–15/month or per-export pricing. Validate willingness to pay with real cohort.

---

## 11. Open Questions

1. Do AI music creators actually want printable charts, or just playback?
2. Is simplification more valuable than transcription accuracy to this user?
3. What is the minimum output quality required to feel superior to MuseScore import?
4. Is MIDI-first sufficient, or does audio input need to come earlier than expected?

---

## 12. Out of Scope (Permanent or Long-Term)

- Audio transcription — deferred, not permanent. Target Phase 3–4.
- Real-time collaboration
- DAW plugin
- Full arrangement / multi-instrument scores
- AI reharmonization or style transfer

---

*This document is the source of truth for V1 scope. Any feature not listed under V1 must go through a scope change discussion before being added.*
