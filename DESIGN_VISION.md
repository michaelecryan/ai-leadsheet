# SoloAct — Design Vision

> **Purpose:** This document defines the visual identity, UX architecture, and interaction design for SoloAct's V1 redesign. It is the north star for every UI decision. Implementation should be sequenced by the priority list at the end.

---

## 1. Design Philosophy

**"The song is the hero. The UI is the teacher."**

SoloAct sits at the intersection of music software and education. Most music tools are built for people who already identify as musicians — they expose complex controls, assume literacy, and optimise for power. SoloAct is built for the moment *before* someone thinks of themselves as a musician.

Three principles govern every design decision:

1. **Clarity over density.** A non-musician should never have to parse competing information. One thing at a time, presented with confidence.
2. **Reveal, don't overwhelm.** "Your song in 4 chords" is a revelation. The design must make that moment feel like a magic trick, not a spreadsheet.
3. **Earned complexity.** Simple by default. Detail is available but never imposed. The bar-by-bar grid exists for people who want it — it should never be the first thing anyone sees.

### Design references
- **Linear** — information density without clutter, dark mode done right, tasteful motion
- **Spotify** — the audio player as a persistent, confident UI element; album art as hero
- **Notion** — clean typography hierarchy, generous whitespace, content-first
- **Soundslice** — synced playback with notation; proves the concept works beautifully when done well

### What SoloAct is NOT
- Not a DAW (no timeline, no tracks, no waveform editing)
- Not a notation app (no staff, no clefs, no key signatures rendered as notation)
- Not a practice tool for advanced musicians (no stem separation, no metronome, no loop controls in V1)

---

## 2. Visual Identity

### 2.1 Color System

**Dark mode by default.** The entire product lives on a near-black canvas. This is a music tool — dark mode is native to the domain (Spotify, Ableton, Logic, every DAW). It also makes chord diagrams and the accent color pop.

| Role | Token | Hex | Usage |
|---|---|---|---|
| Background | `--bg` | `#0A0A0B` | Page canvas. Slightly cooler than current `#0f0f0f` for more depth. |
| Surface | `--surface` | `#141416` | Cards, modals, elevated containers |
| Surface raised | `--surface-raised` | `#1C1C1F` | Hover states, active cards, player bar |
| Border subtle | `--border` | `#2A2A2E` | Card edges, dividers |
| Border hover | `--border-hover` | `#3A3A40` | Interactive element hover |
| **Accent** | `--accent` | `#3EDB8C` | **Primary CTA, active states, chord highlights.** Replaces purple `#6c63ff`. Fresh, energetic, music-native green. |
| Accent hover | `--accent-hover` | `#32C47A` | Buttons on hover, pressed states |
| Accent muted | `--accent-muted` | `rgba(62, 219, 140, 0.12)` | Accent backgrounds (capo banner, active chord card) |
| Accent text | `--accent-text` | `#5AEEA0` | Accent-colored text on dark backgrounds (higher contrast than accent on dark) |
| Text primary | `--text` | `#EDEDEF` | Headlines, chord names, key display |
| Text secondary | `--text-secondary` | `#8B8B92` | Descriptions, labels, timestamps |
| Text muted | `--text-muted` | `#55555C` | Tertiary info, bar numbers |
| Danger | `--danger` | `#EF4444` | Errors, destructive actions |
| Warning | `--warning` | `#F59E0B` | Rate limit notices, trial expiry |

**Rationale for green accent:** The current purple (`#6c63ff`) is generic SaaS. The green (`#3EDB8C`) sits between Supabase green and Chrome's tab group green — it feels fresh, energetic, and distinctive. On a dark canvas it has excellent contrast and draws the eye to exactly the right things: play button, active chord, CTA buttons.

### 2.2 Typography

**Two-font system.** One humanist sans for UI, one monospace for musical data.

| Role | Font | Weight | Usage |
|---|---|---|---|
| **UI text** | Inter | 400, 500, 600, 700 | All interface text, headlines, labels, body copy |
| **Musical data** | JetBrains Mono | 500, 700 | Chord symbols (Am, G, C), key signatures, BPM, time signatures |

**Why monospace for chords?** Chord symbols are data, not prose. Monospace gives them a distinctive, "decoded" look — like the system has extracted something precise from the audio. It also ensures consistent widths in the chord strip, which matters for playback sync alignment.

**Type scale (desktop):**

| Element | Size | Weight | Font |
|---|---|---|---|
| Page headline | 2rem / 32px | 700 | Inter |
| Section headline | 1.25rem / 20px | 600 | Inter |
| Key display | 2.5rem / 40px | 700 | JetBrains Mono |
| Chord name (hero) | 1.5rem / 24px | 700 | JetBrains Mono |
| Chord name (strip) | 1rem / 16px | 600 | JetBrains Mono |
| Body / description | 0.9375rem / 15px | 400 | Inter |
| Label (uppercase) | 0.6875rem / 11px | 600 | Inter |
| Caption | 0.75rem / 12px | 400 | Inter |

### 2.3 Spacing & Layout

- **Max content width:** 880px (up from 720px — needs breathing room for the result page's multi-column layout)
- **Grid:** 12-column with 16px gutters on desktop; collapses to single column on mobile
- **Section spacing:** 32px between major sections, 16px within sections
- **Card padding:** 20px–24px
- **Border radius:** 12px for cards, 8px for buttons, 20px for the player bar

### 2.4 Motion

Subtle, purposeful. Never decorative.

| Element | Animation | Duration | Easing |
|---|---|---|---|
| Page sections appearing (results load) | Fade up + scale from 0.97 | 400ms | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Active chord highlight | Background color transition | 200ms | `ease-out` |
| Chord strip scroll (auto-scroll during playback) | Smooth scroll | continuous | `linear` |
| Button hover | Background shift | 150ms | `ease` |
| Modal open | Fade in + scale from 0.95 | 250ms | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Loading skeleton pulse | Opacity oscillation | 1.5s | `ease-in-out` infinite |

### 2.5 Iconography

No emoji in the product UI. Use a minimal SVG icon set (Lucide or Phosphor) for:
- Play/pause, skip, speed control (player)
- Upload, link (input methods)
- Save, share, external link (actions)
- Music note, guitar (decorative, sparingly)

Emoji is reserved for the landing page feature strip only if needed for quick visual scanning — but prefer custom SVG icons there too.

---

## 3. Competitive Teardown — Key Findings

### Chordify
- **Strengths:** Instant gratification (paste URL, see chords), real-time playback sync with YouTube video, strong freemium model
- **Weaknesses:** Assumes musical literacy, chord diagrams are small and secondary, light mode feels dated, overwhelming premium upsell, no education layer
- **Visual:** Light-mode default, orange accent, functional but not beautiful

### Ultimate Guitar
- **Strengths:** Massive content library, strong community, established brand
- **Weaknesses:** Ad-heavy, no audio processing (text-only tabs), dated visual design, no beginner framing, no AI-native workflow
- **Visual:** Dark-ish theme with orange/yellow accent, cluttered layout, banner ads

### Moises
- **Strengths:** Best-in-class AI separation, polished mobile app, comprehensive practice tools (loop, speed, key shift)
- **Weaknesses:** Complex control surface overwhelms beginners, positioned as a power tool, no education/lesson layer, expensive ($9.99–13.99/mo)
- **Visual:** Dark mode, blue/purple accent, dense but well-organized, Spotify-like audio player

### ChordAI
- **Strengths:** Real-time chord detection, shows fingerings, clean mobile UI, affordable
- **Weaknesses:** Mobile-only (no desktop experience), assumes guitarist identity, no play-along sync in the Suno/Udio sense, no education layer
- **Visual:** Dark mode, teal accent, mobile-native design

### Soundslice
- **Strengths:** Best notation sync implementation, used by professional educators, excellent playback controls
- **Weaknesses:** Built for music-literate users, intimidating notation, no audio upload (requires pre-made notation), expensive for publishers
- **Visual:** Light mode, clean but clinical, notation-heavy

### The gap SoloAct owns

**No competitor serves the pre-musician.** Every tool above assumes the user already identifies as a player. SoloAct is the only product designed for the identity transformation moment — "I just made a song with AI and I want to learn to play it." This means:

1. **Beginner-first information design** — chord diagrams are the hero, not a sidebar
2. **Education is core, not a bolt-on** — the theory lesson and lesson links aren't features, they're the product
3. **The song as motivation** — every competitor treats the song as input; SoloAct treats it as the emotional hook that makes someone pick up a guitar

---

## 4. User Persona Audit — Current UI

### Persona 1: AI Music Maker (Primary)
**Job:** "Help me understand my song and give me a path to play it."

| What works | What fails |
|---|---|
| "Your song in X chords" revelation | Information hierarchy is flat — everything has equal weight |
| Chord diagrams with finger positions | Player bar is buried below diagrams — aha moment requires scrolling |
| Plain English key explanation | Bar-by-bar grid overwhelms beginners (40+ grey boxes) |
| Lesson links as clear next step | Theory micro-lesson is easy to miss |
| | Loading state feels broken (spinner + text, no progress) |
| | No emotional payoff — result page is data, not revelation |
| | Feature strip uses emoji — looks amateur |

### Persona 2: Singer/Songwriter using AI
**Job:** "Give me something clean I can hand to another musician."

| What works | What fails |
|---|---|
| Public sharing via link | No song title input on upload |
| Key + chords are accurate | No transposition control |
| Bar-by-bar grid is correct format | No section markers (verse/chorus/bridge) |
| | No PDF export (Phase 7) |
| | Shared view has no playback for recipient |

### Persona 3: Music Teacher
**Job:** "Turn this song into a lesson plan I can work from."

| What works | What fails |
|---|---|
| Theory micro-lesson is a start | No section annotations |
| Lesson links are relevant | Theory is AI-generated, not editable |
| Chart storage/sharing works | No ability to simplify chord set for lesson |
| | No student handout / PDF |
| | Dashboard has no organization tools |

---

## 5. Core Result Page — The Hero Moment

This is the most important screen in the product. A user just waited 20–40 seconds. The result page must immediately deliver the "magic trick" — your complex-sounding song is just 4 chords. Here's how to play them. Press play and follow along.

### 5.1 Layout (1280×800 viewport — above the fold)

```
┌─────────────────────────────────────────────────────────┐
│  SoloAct                          [My charts] [Save]    │  ← Sticky header, 48px
├─────────────────────────────────────────────────────────┤
│                                                         │
│  A minor                                                │  ← Key display (large, monospace)
│  Darker, more emotional feel · 120 BPM · 4/4            │  ← Meta line (one row)
│                                                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │  ▶  ━━━━━━━━━●━━━━━━━━━━━━━━━━━━━  1:24 / 3:12    ││  ← Sticky player bar
│  │     Am        G         F         C        Am       ││  ← Chord strip (synced, scrolling)
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  Your song in 4 chords                                  │  ← Hero heading
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   │
│  │  Am  │ │  G   │ │  F   │ │  C   │                   │  ← Chord cards with SVG diagrams
│  │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │                   │
│  │ │  │ │ │ │  │ │ │ │  │ │ │ │  │ │                   │
│  │ │••│ │ │ │••│ │ │ │••│ │ │ │••│ │                   │
│  │ └──┘ │ │ └──┘ │ │ └──┘ │ │ └──┘ │                   │
│  └──────┘ └──────┘ └──────┘ └──────┘                   │
│                                                         │
│  ── About this progression ──────────────────────────── │  ← Theory micro-lesson
│  Am → G → F → C is one of the most common progressions  │
│  in pop music...                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
  ── Below the fold ──────────────────────────────────────
  Learn these chords (lesson cards)
  Full progression — bar by bar (collapsible, closed by default)
  Capo suggestion (if applicable)
  Scales to solo over this
```

### 5.2 Key Design Decisions

**1. Player bar is persistent and contains the chord strip.**
The player bar sits between the key display and the chord diagrams. It is `position: sticky` so it remains visible when scrolling. Critically, it includes a **chord strip** — a horizontal row of chord symbols that scroll in sync with playback. The currently-playing chord is highlighted with the accent color. This is the play-along mechanism: the user looks at the chord strip to know what chord to play NOW, and looks at the diagrams below to know HOW to play it.

**2. Chord diagrams are large and above the fold.**
The "Your song in X chords" section with SVG diagrams must be visible at 1280×800 without scrolling. Maximum 6 chords displayed. Each card shows: chord name (large, monospace), SVG finger diagram, and a subtle "learn" link.

**3. Theory micro-lesson is visible, not hidden.**
Positioned directly below the chord diagrams with a clear section header. This is not a collapsible panel or a tooltip — it's core content. The progression summary is the most prominent field; emotional character and beginner takeaway are secondary.

**4. Bar-by-bar grid is below the fold, collapsed by default.**
The grid is still available for Persona 2 and 3, but it does not compete with the hero moment for Persona 1. A "Show full progression" toggle reveals it. When expanded, the currently-playing bar highlights during playback.

**5. Meta information is compressed into one line.**
Key, BPM, and time signature are shown on a single line below the key display — not as separate cards. This reduces visual clutter significantly.

**6. The chord strip replaces the bar-by-bar grid as the primary play-along mechanism.**
Instead of highlighting cards in a 4-column grid, the chord strip is a single horizontal timeline that auto-scrolls. Each chord block is sized proportionally to its duration. This is far more intuitive for following along.

### 5.3 The Chord Strip — Detailed Design

The chord strip is the most novel UI element. It sits inside the player bar and provides the karaoke-style play-along experience.

```
┌──────────────────────────────────────────────────────────┐
│  ▶  ━━━━━━━━━━━●━━━━━━━━━━━━━━━━━━━━━━  1:24 / 3:12  1x │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐      │
│  │ Am  │ Am  │ G   │ G   │ F   │ F   │ C   │ C   │ ···  │
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘      │
└──────────────────────────────────────────────────────────┘
```

- Each block represents one bar
- Block width is proportional to duration (most bars are equal, but a held chord shows as a wider block)
- The active block has accent background (`--accent-muted`) and accent left border
- The strip auto-scrolls to keep the active chord centered
- Chord names use JetBrains Mono for consistent width
- When a chord changes, the corresponding hero diagram below gets a subtle highlight ring

### 5.4 Key Display

```
A minor
Darker, more emotional feel · 120 BPM · 4/4
🎸 Tip: Capo on fret 3 — play in G shapes
```

- Key name: 2.5rem, JetBrains Mono, 700 weight, white
- Plain English + meta: one line, Inter 400, `--text-secondary`
- Capo tip: accent-muted background, accent text, only shown when applicable
- No separate "KEY" label — the information speaks for itself

---

## 6. Landing Page — Before the Song

### 6.1 Hero Section

```
┌─────────────────────────────────────────────────────────┐
│  SoloAct                                    [Sign in]   │
│                                                         │
│         Your AI song.                                   │
│         Your first guitar lesson.                       │
│                                                         │
│  Upload a track from Suno, Udio, or any audio file.     │
│  See the chords. Learn to play. Follow along in sync.   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │                                                 │    │
│  │     ┌─┐    Drop your track here                 │    │
│  │     └─┘    or click to browse                   │    │
│  │                                                 │    │
│  │     MP3 · WAV · FLAC · OGG · M4A · MIDI        │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│   │ Chord    │  │ Play     │  │ Learn    │             │
│   │ diagrams │  │ along    │  │ from     │             │
│   │          │  │          │  │ lessons  │             │
│   └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

- Hero headline is 2.5rem, centered, tight line-height
- Sub-copy is `--text-secondary`, max 480px wide
- Drop zone has a dashed border, subtle icon, generous padding
- Feature strip uses custom SVG icons (not emoji), muted text, concise labels
- The entire above-the-fold area has one CTA: upload your track

### 6.2 Social Proof (below fold, future)
- "Join X people learning guitar from their AI songs"
- Example chord chart screenshot/animation
- Testimonial from r/SunoAI if available

---

## 7. Processing State — The 20–40 Second Wait

This is where most users churn. The current spinner + text is insufficient. The wait needs to feel purposeful, not broken.

### 7.1 Skeleton Loading with Staged Reveals

Instead of a spinner, show a skeleton of the result page that fills in as processing completes:

**Stage 1 (0–5s):** "Listening to your track..." — waveform animation (a simple CSS sine wave, not a real waveform)

**Stage 2 (5–15s):** "Finding the key..." — the key skeleton placeholder pulses, then resolves to the actual key. First piece of real data appears. User sees progress.

**Stage 3 (15–25s):** "Detecting chords..." — chord cards skeleton shows 4–6 placeholder cards pulsing

**Stage 4 (25–35s):** "Building your chart..." — everything resolves. Chord strip appears, diagrams populate, player becomes active.

### 7.2 Copy

The loading copy should feel conversational and confident:
- "Listening to your track..." (not "Processing audio" or "Transcribing")
- "Finding the key..." (not "Running key detection algorithm")
- "This usually takes 20–30 seconds"

### 7.3 Fallback

If processing exceeds 45 seconds, show: "Taking longer than usual — complex tracks need a bit more time. Almost there."

If processing fails: clear error with a retry button and a support email. Never show a stack trace or technical error.

---

## 8. Empty & Error States

### 8.1 Empty Dashboard
"No charts yet. Upload your first track to get started."
— Big, centered, with a prominent upload CTA button (not just a text link)

### 8.2 Upload Error
Red-tinted card with clear language:
- "We couldn't process this file" — followed by likely cause
- "This file is too large (max 20MB)" — for 413 errors
- "This file type isn't supported" — for 415 errors
- "You've hit the upload limit — try again in an hour" — for 429 errors
- Always include: "Try a different file" button

### 8.3 Chart Not Found (shared link)
"This chart doesn't exist or has been removed."
— With a CTA: "Create your own chord chart →"

### 8.4 Network Error
"We lost the connection. Check your internet and try again."
— With retry button

---

## 9. Mobile Considerations

V1 is desktop-first, but the layout should not break on mobile. Key decisions:

- **Single-column layout** on screens < 768px
- **Chord strip scrolls horizontally** (same as desktop, just narrower)
- **Chord diagrams stack 2 per row** on mobile (not horizontal scroll — too fiddly with touch)
- **Player bar remains sticky** at the bottom on mobile (not the top — thumb reach)
- **Theory section and lessons** remain visible but less prominent
- **Bar-by-bar grid** is hidden on mobile entirely (accessible via "Show full progression")
- **Upload:** file picker only on mobile (no drag-and-drop). URL input is prominent since mobile users are more likely to paste a Suno share link.

---

## 10. Component Inventory

### Core Components

| Component | Description | Status |
|---|---|---|
| `PlayerBar` | Sticky player with progress, play/pause, speed, chord strip | Redesign |
| `ChordStrip` | Horizontal timeline of chord blocks, synced to playback | New |
| `ChordCard` | Card with chord name + SVG diagram | Redesign |
| `KeyDisplay` | Large key name + plain English + meta row | Redesign |
| `TheoryLesson` | Progression summary + fields card | Redesign |
| `LessonCards` | Horizontal scroll of chord → lesson links | Minor update |
| `DropZone` | File upload area with drag-and-drop | Redesign |
| `LoadingSkeleton` | Staged skeleton loading with progress text | New |
| `ChordGrid` | Bar-by-bar grid (collapsible) | Redesign |
| `NavBar` | Logo + auth state + actions | Minor update |
| `CapoBanner` | Capo suggestion with accent styling | Minor update |

### Shared Design Tokens (CSS custom properties)

All colors, spacing, and typography values should be defined as CSS custom properties in a `:root` block. This enables future theming and ensures consistency across pages (`index.html`, `chart.html`, `dashboard.html`).

---

## 11. Prioritised UI Changes — Current → Vision

Sequenced by user impact. Each item is an atomic, shippable change.

### Tier 1 — Launch Blockers (ship before public launch)

| # | Change | Impact | Effort |
|---|---|---|---|
| 1 | **Replace purple accent with green** (`#6c63ff` → `#3EDB8C`) globally | Brand identity, distinctiveness | Low — find/replace + per-component tuning |
| 2 | **Add chord strip to player bar** | The play-along "aha" moment. Most important UX improvement. | High — new component, playback sync logic |
| 3 | **Make player bar sticky** (`position: sticky`) | Player visible while viewing diagrams | Low |
| 4 | **Redesign loading state** — skeleton + staged progress copy | Reduces churn during processing wait | Medium |
| 5 | **Collapse bar-by-bar grid** behind a toggle, closed by default | Reduces beginner overwhelm | Low |
| 6 | **Compress meta into single line** (remove separate meta cards) | Cleaner result page, more room for hero content | Low |
| 7 | **Switch to Inter + JetBrains Mono** typography | Professional feel, chord symbols as data | Low — font imports + CSS |
| 8 | **Replace emoji icons** in feature strip with SVG icons | More professional, trustworthy | Low |

### Tier 2 — High Impact (ship within first week post-launch)

| # | Change | Impact | Effort |
|---|---|---|---|
| 9 | **Redesign chord cards** — larger diagrams, "learn" link on each card | Better above-the-fold readability | Medium |
| 10 | **Enhance theory micro-lesson** visibility — section header, card redesign | Core educational content becomes more prominent | Low |
| 11 | **Add song title input** (editable on save) | Charts are identifiable in dashboard and shares | Low |
| 12 | **Redesign landing page** — remove emoji, refine copy, add personality to drop zone | Better first impression, higher upload conversion | Medium |
| 13 | **Extract CSS custom properties** for all design tokens | Foundation for consistency across all pages | Medium |
| 14 | **Animate result page load** — sections fade in sequentially | Polished feel, draws attention in right order | Low |

### Tier 3 — Polish (ship within first month)

| # | Change | Impact | Effort |
|---|---|---|---|
| 15 | **Redesign dashboard** — better chart cards, search, organization | Returning user experience | Medium |
| 16 | **Redesign chart.html** (shared view) — match new result page design | Shared charts look as good as owner's view | Medium |
| 17 | **Mobile responsive pass** — single column, sticky bottom player, 2-col chord grid | Mobile users can at least view results | Medium |
| 18 | **Redesign auth modal** — cleaner, fewer steps, match new brand | Conversion rate on sign-up | Low |
| 19 | **Redesign error states** — better copy, clear recovery actions | Reduces support load | Low |
| 20 | **Add subtle motion** — hover states, transitions, section entrances | Premium feel | Low |

### Tier 4 — Future (V2+)

| # | Change | Impact | Effort |
|---|---|---|---|
| 21 | Section markers in bar-by-bar grid (verse/chorus/bridge) | Persona 2 & 3 need | High |
| 22 | Transpose control | Persona 2 need | Medium |
| 23 | PDF export with new design system | Persona 2 & 3 need | High |
| 24 | Light mode toggle | Accessibility, some users prefer | Medium |

---

## 12. Design System Summary

### Quick Reference

```css
:root {
  /* Colors */
  --bg: #0A0A0B;
  --surface: #141416;
  --surface-raised: #1C1C1F;
  --border: #2A2A2E;
  --border-hover: #3A3A40;
  --accent: #3EDB8C;
  --accent-hover: #32C47A;
  --accent-muted: rgba(62, 219, 140, 0.12);
  --accent-text: #5AEEA0;
  --text: #EDEDEF;
  --text-secondary: #8B8B92;
  --text-muted: #55555C;
  --danger: #EF4444;
  --warning: #F59E0B;

  /* Typography */
  --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 20px;

  /* Transitions */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
}
```

### Font Loading

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
```

---

*This document is the source of truth for SoloAct's visual design. Every UI change should reference it. Update it as decisions evolve.*
