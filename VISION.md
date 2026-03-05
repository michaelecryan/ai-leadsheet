# ai-leadsheet — Product Vision

> This document captures long-term product direction and blue-sky thinking.
> It is NOT a backlog. Nothing here gets built until it's moved into the PRD.
> Updated as thinking evolves.

---

## The One-Line Vision

**Your AI song as your first music lesson.**

---

## The Sharpest Wedge (Updated Thinking — 2026-03-05)

The original positioning was: guitarist uses Suno, can't play their song, needs a chord chart.

The sharper positioning is: **the music-curious non-musician.**

This person just discovered Suno. They're generating songs they genuinely love — for the first time in their life they're thinking "I wonder if I could actually learn to play this." They're not a guitarist yet. They don't have Chordify in their workflow. They don't know what a chord progression is. But they're motivated in a way they've never been before — because *they made this song.*

That's a fundamentally different user than the intermediate guitarist who already has tools. And it's a bigger, less contested market.

**The core experience for this person:**

1. Make a song in Suno
2. Drop it into the tool
3. Here's the key — here's what that means in plain English
4. Here are the 4 chords in this song — here's how to play them on guitar (chord diagrams, fingerings)
5. Here's the scale you'd use to solo over it
6. Press play and follow along — chords highlight in sync
7. Here are JustinGuitar / Marty Music videos showing you exactly how to play these chords and this style

The song is the hook. The education is the product. The AI generation is what makes it personal and motivating in a way generic guitar lessons never were.

**Why this is better than targeting existing guitarists:**
- Existing guitarists already have Chordify, Ultimate Guitar, Moises
- The music-curious non-musician has nothing purpose-built for them
- Their motivation is higher — it's *their* song
- The education layer is the natural upsell, not a bolt-on

---

## Where This Starts

Upload audio → get key + chords + scale recommendations + educational resources + play along in sync.

Simple, fast, useful in one session. Targeted at the AI music boom while it's still early.

---

## Where This Could Go

The wedge opens into something much bigger if the core loop works.

### Phase 1 — The AI Music Utility
The current build. Audio in, chord chart out, play along. Guitar-optimised. Positioned squarely at the Suno/Udio user who plays an instrument.

### Phase 2 — The Guitarist's Practice Tool
Once you have chord charts and audio playback, you're one step away from a full practice environment:
- Loop sections
- Slow down playback without changing pitch
- Transpose to a different key
- Set a metronome over the track
- Export chart as PDF to print

This is the Guitar Pro / Moises lane, but lighter and more focused on AI-generated content.

### Phase 3 — The Music Education Layer
This is not a Phase 3 add-on — it is the retention mechanism and ships alongside playback sync.

The same chord chart infrastructure that helps someone play along also teaches them. Instead of building a course, the product routes users to contextual lessons from trusted creators that match exactly what was detected in their song:

- "These are the 4 shapes in your song — here's Justin's Grade 1 lesson that teaches exactly those"
- "This groove uses a common strumming pattern — here's that Marty video, then come back to play along"
- What scale fits over this progression for soloing
- How to recognise common patterns (I-IV-V, ii-V-I) in other songs they know

Education sources: JustinGuitar, Marty Music, and potentially piano equivalents (Skoove, OnlinePianist) as the product expands.

This is the angle the Guitar App guys (Ireland) were building toward. The idea of contextual education — "here's your chord progression, here's the lesson that teaches it" — is genuinely powerful and nobody has nailed it for AI-generated music.

### Phase 4 — The Community Layer
Charts shouldn't stay private. If someone processes a Suno track and gets a clean chart, that chart has value to every other guitarist who generated the same song — or a similar one.

Possible community directions:
- Public chart library — browse charts other users have generated
- Rate and improve charts — crowdsourced quality improvement
- "I'm playing this" — see who else is working on the same song
- Collaborative jamming — stretch goal, but interesting long-term

This starts to look like Ultimate Guitar but for AI-generated music. Ultimate Guitar's moat is their catalogue — millions of human-uploaded tabs. The equivalent moat here is AI-generated chart data at scale.

### Phase 5 — Platform Integrations
- **Spotify** — detect chord progressions from any Spotify track, not just AI-generated audio. Massive TAM expansion. "Learn any song on Spotify" is a very different product than "learn your Suno song."
- **YouTube** — sync chord charts to YouTube videos. Watch a performance, follow the chords. Educational content integration.
- **Suno/Udio direct** — if they ever open APIs, deep integration makes sense. One-click from generated song to playable chart.
- **GuitarTuna / Fender Tune** — partnership or acquisition target if this gets traction. They have the user base, we have the AI workflow.

---

## The Competitive Arc

**Now:** Filling a gap nobody else has targeted — AI-generated audio → guitarist workflow.

**12 months:** Competing with Chordify on chord detection quality, but with better guitar UX and AI-native positioning.

**2-3 years:** Competing with Moises on the practice tool layer. Competing with Ultimate Guitar on the community/catalogue layer. But with a differentiated origin story — built for the AI music generation era, not retrofitted to it.

**Long term:** The music education angle is the biggest potential surface area. The intersection of AI-generated music + contextual guitar education + community is a space nobody owns yet. It's the difference between a utility tool and a platform.

---

## The User Evolution

**V1 user:** The music-curious non-musician. Uses Suno/Udio to generate songs, has never played guitar, but is motivated to learn because it's *their* song. Wants the key, the chords, how to play them, and a play-along experience. Does not know what Chordify is.

**V2 user:** The beginner guitarist. Has been playing 6-12 months, uses Suno for backing tracks and practice material. Wants chord charts, scale recommendations, and contextual lessons.

**V3 user:** The intermediate guitarist. Already has tools but comes for the AI-native workflow and education layer. Wants deeper theory, improvisation guidance, and community.

**V4 user:** Community member who shares charts, rates them, discovers new songs through other players.

---

## The Business Arc

- **V1:** $5–10/month subscription. 100–200 users. Prove the loop works.
- **V2:** $10–15/month. Practice tools justify higher price. 500–1000 users.
- **V3:** Freemium with education layer as premium. Potentially ad-supported free tier (contextual YouTube lesson recommendations = natural ad surface).
- **V4:** Community network effects change the business model. Catalogue value. Potential for licensing, partnerships, or acquisition interest from music ed platforms.

---

## The Name

"ai-leadsheet" is a dev handle, not a product name. When the time comes, the name should reflect the broader vision — not just the lead sheet output, but the play-along, learn-along experience.

Worth thinking about when V1 has traction.

---

## Things Worth Watching

- **Suno/Udio API roadmap** — direct integration changes everything
- **Guitar Pro** — if they add AI audio input, they're a direct competitor with a huge install base
- **Moises** — they're the closest comp and well-funded. Watch what they build next.
- **AI music generation quality** — as Suno/Udio output gets better, the transcription problem gets easier. That's a tailwind.
- **Music education market** — growing, underserved digitally, high willingness to pay

---

*This is a living document. Add to it when something feels worth keeping. Don't act on it until it's in the PRD.*
---

## The Core Product Challenge

Non-musicians upload Suno tracks that sound lush, layered, and complex. The job of the product is to say: **"This sounds complicated. It isn't. Here are 4 chords."**

That's the magic trick. That's what moves someone from "I could never play this" to "wait, I could actually do this."

This is not just a technical problem — chord simplification is already in the pipeline. It's a **UX and communication problem.** How do you present simplification as a revelation rather than a disappointment?

Design principles to hold:
- **"Your song in 4 chords"** as the hero moment — big, confident, simple. Not a staff, not a chord chart. Just 4 big boxes with finger diagrams.
- **Side-by-side audio** — "Here's your full song. Here's what it sounds like with just these 4 chords." The moment of recognition is everything.
- **Contextualise, don't diminish** — Am, G, F, C is hundreds of hit songs. That's not a limitation, it's an invitation. "The same chords as [famous song they know]."
- **Never show complexity you don't need to.** The Moises control surface terrifies this user. Hide everything that doesn't serve the beginner moment.

---

## Competitive Risk Stories

### Risk 1: Chord AI slides down into the wedge
Chord AI already does chord/key/tempo detection and shows fingerings for guitar, piano, ukulele. They market "learn any song" and explicitly target novices. Adding a "Beginner mode" and a Suno/Udio import funnel is cheap and fast for them.

**Implication:** Move fast on brand and narrative. Don't be "another chord detector" — be "your AI song as your first lesson" everywhere. Over-index on teaching UX for total beginners so it's not copyable with a toggle.

### Risk 2: Moises adds an "AI song beginner lane"
Moises already has stems, looping, slow-down, chord detection, key shift. Their practice stack is already better than what can be shipped in year one. If they decide AI-song creators are a growth segment, they can bundle the wedge as a practice preset.

**Implication:** Make identity shift and education the defensible layer. Moises is designed for people who already practice. Design from the ground up for "I don't play at all yet." Never expose the full control surface early.

### Risk 3: Lesson platforms wrap around AI songs
JustinGuitar, Yousician, Fender Play already have structured beginner paths, progress tracking, and community. Adding "import your Suno song" + auto chord detection drops users into their existing curriculum. Their weakness is ingest and detection — both solvable.

**Implication:** Edge is in deeply binding the song and the lesson together, not using AI tracks as bait. If this works, it becomes a natural acquisition target for these platforms — they want the validated "AI song → first lesson" funnel.

### Shared weakness across all three risks
None of these products are built from the ground up for **identity transformation** — the moment before someone thinks of themselves as a musician. That's genuinely hard to retrofit. That's the defensible core.

---

## Research Validation (2026-03-05)

**Source:** Perplexity deep research on AI music communities and guitarist behaviour.

Key findings:
- Organic signal confirmed: Suno/Udio users are explicitly saying AI songs made them want to learn a real instrument
- The workflow is already being hacked: users exporting Suno tracks, asking for chord detection, wanting playable chords for their own creations
- Educators are using Suno/Udio as classroom engagement hooks — validates "your song as teaching entry point" but nobody has built a structured instrument-learning product around it
- Nobody owns the wedge: pieces of the stack exist (generate → chords → practice → lessons) but no product is explicitly built around "music-curious non-musician uses their AI song as their first guitar/piano lesson"
- Community features are a distraction pre-PMF. Prove the individual loop first.

**PMF bar:** Consistent inbound from the "I made a Suno song and want to learn to play it" narrative. Repeat uploads and lessons from the same user. Evidence of identity shift — not one-off novelty.
