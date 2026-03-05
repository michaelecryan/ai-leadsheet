# AI Lead Sheet — Product Requirements Document

**Version:** 1.3
**Status:** Active
**Last Updated:** 2026-03-05

---

## 1. Problem

AI music tools like Suno and Udio let anyone generate a song — including people who have never thought of themselves as musicians. For many of these users, making a song with AI sparks something new: a genuine curiosity about music, and a desire to understand and play what they've created.

But there's no on-ramp for them. The tools that exist — Chordify, Chord AI, Moises — are built for people who already play. They assume musical literacy. They expose controls and terminology that overwhelm a total beginner.

The result: a motivated, curious non-musician hits a wall. They export their Suno track, try to hack together a workflow (YouTube → Chordify → generic lesson video), and most give up before they play a single chord.

**The specific gap:** No product is built around the journey from "I just made a Suno song" to "I just played my first chord on a real guitar." That journey — your AI song as your first music lesson — is unoccupied.

**The market reality:** Suno/Udio MIDI export requires a paid plan (~$10/month). Audio export is free for all users. Audio is the primary input path — it reaches a significantly larger audience and produces good enough output on synthesized AI audio.

---

## 2. Solution

**AI Lead Sheet** takes a Suno or Udio song and turns it into a non-musician's first guitar lesson — automatically.

Upload your AI song. Get the key (explained in plain English). Get the 3–5 chords in the song (shown as big, simple finger diagrams). Press play and follow along as chords highlight in sync. Then get pointed to the exact JustinGuitar or Marty Music video that teaches those chords.

The core magic trick: a song that sounds complex is usually 4 chords. The product's job is to reveal that simplicity in a way that feels like a revelation, not a disappointment.

**"Your song in 4 chords."** That's the hero moment.

---

## 3. Persona

**Primary User: The Music-Curious Non-Musician**

- Uses Suno or Udio to generate songs — and loves it
- Has never played guitar (or gave up years ago)
- For the first time, feels motivated to learn — because it's *their* song
- Does not know what Chordify is. Does not know what a chord progression is.
- Wants to understand what they've made and play at least part of it
- Will churn fast if the first 15 minutes don't deliver a genuine "I'm doing it" moment

**They are not:**
- An intermediate guitarist who already has tools
- A producer needing stems or MIDI editing
- Someone who wants a full music theory course

**Design rule:** If a feature makes a total non-musician feel dumb, it belongs in Phase 2+, not V1.

**User evolution:**
- V1 → V2 trigger: user has processed ≥3 songs and opened the chord view for the same song ≥3 times → softly introduce practice mode (looping, slow-down)
- V2 → V3 trigger: user uses practice mode ≥20 minutes/week over 2+ weeks → they're a practicing guitarist now; introduce theory and community

---

## 4. The Core Product Loop

This is the experience we are building toward. Every decision must serve this loop.

1. **Upload** — user drops in their Suno/Udio MP3 or WAV
2. **Understand** — key shown with plain-English explanation; 3–5 chords displayed as large, simple finger diagrams; "Your song in 4 chords" is the hero moment
3. **Play along** — chords highlight in sync with audio playback; no theory knowledge required to follow
4. **Learn** — curated JustinGuitar / Marty Music videos mapped directly to the chords detected in their song

Step 3 is the "aha" moment. Step 4 is the retention mechanism.

**The first 15 minutes determine everything.** The product lives or dies on this window.

**Atomic user stories for V1 (these are acceptance tests, not features):**
- "I dropped in my Suno song and in under 10 seconds I understood: key, 3–5 chords, and where to put my fingers for the first chord."
- "I pressed play and just followed the highlighted chord names on screen without understanding any theory, and it still felt like 'I'm playing my song'."
- "After the first play-through I knew exactly one thing I'd learned (e.g. 'this shape is G', 'this is called the key of C')."

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
| Chord diagrams | ✅ | V1 core — large, simple finger diagrams for non-musicians. Rendered from chord symbols. |
| Melody line | 🔄 | Deprioritised — messy from Basic Pitch; may return Phase 2 |
| Full piano voicings | ❌ | Not in V1 — piano voicings planned for later phase as product expands beyond guitar |
| Bass line | ❌ | Out of scope |
| Drum parts | ❌ | Out of scope |
| Tabs | ❌ | Out of scope for V1 — Phase 8 if demand signals it |

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
- Designed for non-musicians who want to play along, not read notation

---

## 7. Competitive Landscape

| Product | Who it's for | Core job | Gap |
|---|---|---|---|
| Chordify | People who already play guitar/keys | "I want chords for this track, fast." | Assumes musical literacy; no beginner UX; no education layer |
| Moises | Practicing musicians and producers | "I want stems, key, tempo, and control." | Power tool complexity overwhelms non-musicians; no identity on-ramp |
| Ultimate Guitar | Guitarists learning existing songs | "I want tabs/lessons for songs I know." | No audio processing; human-uploaded only; not AI-native |
| Chord AI | Guitarists learning any song | "Detect chords from any audio." | Assumes you identify as a guitarist; no beginner framing |
| MuseScore | Musicians needing full transcription | "I want accurate notation." | Not optimised for playability; no play-along |
| **ai-leadsheet V1** | **Music-curious Suno/Udio users (non-players)** | **"I want to play my AI song as my first lesson."** | **Nobody owns this** |

**Shared weakness across all competitors:** None are built from the ground up for identity transformation — the moment before someone thinks of themselves as a musician. That's genuinely hard to retrofit. That's the defensible core.

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
- [x] FastAPI backend (`/health`, `/upload`) — accepts audio/MIDI, returns chord chart JSON
- [x] Chord timestamps in pipeline output (`time_seconds` per chord, drives playback sync)
- [ ] Frontend upload UI — file picker in browser, POSTs to `/upload`
- [ ] Render chord chart from JSON in browser (chord symbols, key, capo hint)
- [ ] Large chord diagrams for non-musicians (ChordJS or equivalent)
- [ ] Audio playback in browser with real-time chord highlighting

### Should Have
- [x] Capo suggestions for guitar-unfriendly keys
- [x] `--inspect` flag for calibration visibility
- [ ] Saved charts (basic, pre-auth)
- [ ] Validation across 5–10 Suno/Udio audio exports (in progress)

### Won't Have in V1
- PDF export (Phase 7)
- User accounts or payment (Phase 5+)
- Advanced reharmonization
- Tab notation (Phase 8)
- Collaboration features
- Piano voicings (later phase — guitar is V1 instrument)

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

**Primary V1 metric:** % of new users who complete one full play-through of their own song and engage with at least one chord along with it.

Everything else is secondary to this behaviour.

**V1 is successful when:**
1. User uploads a Suno/Udio audio file and receives key + chords in under 10 seconds
2. Chord display is immediately readable by someone who has never played guitar (large diagrams, no jargon)
3. Audio plays back with chords highlighting in sync — no theory knowledge required to follow
4. At least one contextual lesson link (JustinGuitar / Marty) is surfaced based on detected chords
5. Validated on 5–10 real Suno/Udio exports across different genres
6. Demo video posted to r/SunoAI — generates genuine comments, not just upvotes

**Early KPI stack:**
- **Activation:** % who upload a second song within 7 days
- **Learning:** % who can answer 1–2 simple in-app chord recognition questions correctly
- **Revenue:** conversion to paid after at least one "I'm actually playing" moment

**Day 2 retention (design before launch, not after):**
Follow-up nudge: "Generate a new Suno song with this prompt — then we'll show you how its chords are different from your first one." Non-musicians churn fast after the initial wow. Engineer the return visit before you ship.

---

## 11. Phase Roadmap

### Phase 1 — CLI Engine ✅ Done
CLI pipeline. Audio or MIDI in, MusicXML out. Simplification, gesture classification, arpeggio detection. Validated on Suno audio exports.

### Phase 2 — Web UI Shell 🔄 Active
FastAPI backend. Upload endpoint. Chord chart rendered in browser (alphaTab). Basic frontend. Deployed to public URL (Railway or Render).

### Phase 3 — Playback Sync 🔄 Active
Audio playback in browser. Chord timestamps from pipeline. Real-time chord highlighting.

### Phase 3b — Education Layer 🔄 Active
Surface contextual JustinGuitar / Marty Music YouTube lessons based on detected chords and song feel. Mapped directly to the user's track — not generic lessons. This is the retention mechanism. Do not defer past Phase 3. Demo video. Community launch (r/SunoAI).

### Phase 4 — Chord Quality
Essentia and Demucs pipeline evaluation in separate branch. Merge best approach. Target: chart accurate enough that a non-musician can follow without second-guessing.

### Phase 5 — User Accounts + Storage
Auth (Clerk or Supabase). Saved charts. Upload history. Dashboard. Prerequisite for charging money.

### Phase 6 — Monetisation
Stripe integration. Free tier (3 uploads/month). Paid tier ($5–10/month, unlimited). Pricing page. Tier enforcement.

### Phase 7 — Output Polish
PDF/printable export. Formatting improvements.

### Phase 8 — Melody Tabs
Fretboard mapper (pitch → string + fret). Only if user demand signals it post-launch.

---

## 12. Open Questions

1. ~~Do AI music creators want printable charts or just playback?~~ **Answered: playback sync is the core feature. Charts are the means, play-along is the end.**
2. ~~Is MIDI-first sufficient, or does audio input need to come earlier?~~ **Answered: audio is primary.**
3. **Desktop-first or mobile-first for V1?** User sitting next to Suno in a browser tab vs. someone on their phone who just generated a track — completely different UX. This decision shapes the entire web shell build. **Needs decision before M1 starts.**
4. What is the minimum chord accuracy required for the play-along to feel useful to a non-musician?
5. Is $5/month or $10/month the right price point for this audience? Non-musicians pay for Fender Play, Yousician — willingness to pay for music education is established.
6. Which JustinGuitar / Marty Music videos to surface first, and how do we map detected chords to the right lesson?

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

**Deferred (not permanent):**
- Piano voicings and piano chord diagrams — planned for later phase once guitar V1 is validated

---

*This document is the source of truth for V1 scope. Any feature not listed under V1 must go through a scope change discussion before being added.*
