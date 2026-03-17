/**
 * soloact-chords.js — Shared chord data and rendering utilities.
 *
 * Loaded by index.html, dashboard.html, and chart.html. Defines:
 *   CHORD_SHAPES     — fret/finger data for ~35 common chords
 *   buildChordSvg()  — renders a chord shape as an inline SVG string
 *   LESSON_LOOKUP    — chord → JustinGuitar + Marty Music lesson URLs
 *   plainEnglishKey() — converts key string to a plain-English description
 */

// ── Chord shape data ──────────────────────────────────────────────────────────
// frets:   [E, A, D, G, B, e] — low string to high string
// fingers: [E, A, D, G, B, e] — finger numbers (1=index, 2=middle, 3=ring, 4=pinky)
// -1 = muted, 0 = open string
// barre: fret number where barre bar is drawn (optional)
// baseFret: starting fret for display (default 1)
const CHORD_SHAPES = {
  // Major open chords
  "C":     { frets: [-1, 3, 2, 0, 1, 0], fingers: [-1, 3, 2, 0, 1, 0] },
  "D":     { frets: [-1, -1, 0, 2, 3, 2], fingers: [-1, -1, 0, 1, 3, 2] },
  "E":     { frets: [0, 2, 2, 1, 0, 0],  fingers: [0, 2, 3, 1, 0, 0] },
  "F":     { frets: [1, 3, 3, 2, 1, 1],  fingers: [1, 3, 4, 2, 1, 1], barre: 1 },
  "G":     { frets: [3, 2, 0, 0, 0, 3],  fingers: [3, 2, 0, 0, 0, 4] },
  "A":     { frets: [-1, 0, 2, 2, 2, 0], fingers: [-1, 0, 1, 2, 3, 0] },
  "B":     { frets: [-1, 2, 4, 4, 4, 2], fingers: [-1, 1, 3, 3, 3, 1], barre: 2, baseFret: 2 },
  "Bb":    { frets: [-1, 1, 3, 3, 3, 1], fingers: [-1, 1, 3, 3, 3, 1], barre: 1, baseFret: 1 },
  // Minor
  "Am":    { frets: [-1, 0, 2, 2, 1, 0], fingers: [-1, 0, 2, 3, 1, 0] },
  "Bm":    { frets: [-1, 2, 4, 4, 3, 2], fingers: [-1, 1, 3, 4, 2, 1], barre: 2, baseFret: 2 },
  "Cm":    { frets: [-1, 3, 5, 5, 4, 3], fingers: [-1, 1, 3, 4, 2, 1], barre: 3, baseFret: 3 },
  "C#m":   { frets: [-1, 4, 6, 6, 5, 4], fingers: [-1, 1, 3, 4, 2, 1], barre: 4, baseFret: 4 },
  "Dm":    { frets: [-1, -1, 0, 2, 3, 1], fingers: [-1, -1, 0, 2, 3, 1] },
  "Em":    { frets: [0, 2, 2, 0, 0, 0],  fingers: [0, 2, 3, 0, 0, 0] },
  "Fm":    { frets: [1, 3, 3, 1, 1, 1],  fingers: [1, 3, 4, 1, 1, 1], barre: 1 },
  "F#m":   { frets: [2, 4, 4, 2, 2, 2],  fingers: [1, 3, 4, 1, 1, 1], barre: 2, baseFret: 2 },
  "Gm":    { frets: [3, 5, 5, 3, 3, 3],  fingers: [1, 3, 4, 1, 1, 1], barre: 3, baseFret: 3 },
  // 7th chords
  "A7":    { frets: [-1, 0, 2, 0, 2, 0], fingers: [-1, 0, 2, 0, 3, 0] },
  "B7":    { frets: [-1, 2, 1, 2, 0, 2], fingers: [-1, 2, 1, 3, 0, 4] },
  "C7":    { frets: [-1, 3, 2, 3, 1, 0], fingers: [-1, 3, 2, 4, 1, 0] },
  "D7":    { frets: [-1, -1, 0, 2, 1, 2], fingers: [-1, -1, 0, 2, 1, 3] },
  "E7":    { frets: [0, 2, 0, 1, 0, 0],  fingers: [0, 2, 0, 1, 0, 0] },
  "G7":    { frets: [3, 2, 0, 0, 0, 1],  fingers: [3, 2, 0, 0, 0, 1] },
  // Major 7
  "Cmaj7": { frets: [-1, 3, 2, 0, 0, 0], fingers: [-1, 3, 2, 0, 0, 0] },
  "Fmaj7": { frets: [-1, -1, 3, 2, 1, 0], fingers: [-1, -1, 3, 2, 1, 0] },
  "Gmaj7": { frets: [3, 2, 0, 0, 0, 2],  fingers: [3, 2, 0, 0, 0, 1] },
  "Amaj7": { frets: [-1, 0, 2, 1, 2, 0], fingers: [-1, 0, 2, 1, 3, 0] },
  // Minor 7
  "Am7":   { frets: [-1, 0, 2, 0, 1, 0], fingers: [-1, 0, 2, 0, 1, 0] },
  "Dm7":   { frets: [-1, -1, 0, 2, 1, 1], fingers: [-1, -1, 0, 2, 1, 1] },
  "Em7":   { frets: [0, 2, 2, 0, 3, 0],  fingers: [0, 2, 3, 0, 4, 0] },
  // Sus / add
  "Dsus2": { frets: [-1, -1, 0, 2, 3, 0], fingers: [-1, -1, 0, 1, 3, 0] },
  "Asus2": { frets: [-1, 0, 2, 2, 0, 0],  fingers: [-1, 0, 1, 2, 0, 0] },
  "Cadd9": { frets: [-1, 3, 2, 0, 3, 0],  fingers: [-1, 3, 2, 0, 4, 0] },
  "Esus4": { frets: [0, 2, 2, 2, 0, 0],   fingers: [0, 2, 3, 4, 0, 0] },
};

// ── SVG chord diagram renderer ────────────────────────────────────────────────
const STRING_GAP  = 22;
const FRET_GAP    = 21;
const PAD_X       = 18;
const PAD_TOP     = 22;
const DOT_R       = 10;
const NUM_STRINGS = 6;
const NUM_FRETS   = 4;

const SVG_W = (NUM_STRINGS - 1) * STRING_GAP + PAD_X * 2;
const SVG_H = NUM_FRETS * FRET_GAP + PAD_TOP + 10;

/**
 * Build an inline SVG string for the given chord symbol.
 * Returns null if the chord is not in CHORD_SHAPES.
 */
function buildChordSvg(symbol) {
  const data = CHORD_SHAPES[symbol];
  if (!data) return null;

  const { frets, fingers, barre, baseFret = 1 } = data;
  const els = [];

  for (let s = 0; s < NUM_STRINGS; s++) {
    const x = PAD_X + s * STRING_GAP;
    els.push(`<line x1="${x}" y1="${PAD_TOP}" x2="${x}" y2="${PAD_TOP + NUM_FRETS * FRET_GAP}" stroke="#444" stroke-width="1.5"/>`);
  }

  for (let f = 0; f <= NUM_FRETS; f++) {
    const y  = PAD_TOP + f * FRET_GAP;
    const sw = (f === 0 && baseFret === 1) ? 4 : 1.5;
    const cl = (f === 0 && baseFret === 1) ? "#999" : "#444";
    els.push(`<line x1="${PAD_X}" y1="${y}" x2="${PAD_X + (NUM_STRINGS - 1) * STRING_GAP}" y2="${y}" stroke="${cl}" stroke-width="${sw}"/>`);
  }

  for (let s = 0; s < NUM_STRINGS; s++) {
    const x    = PAD_X + s * STRING_GAP;
    const fret = frets[s];
    if (fret === 0) {
      els.push(`<circle cx="${x}" cy="${PAD_TOP - 12}" r="6" fill="none" stroke="#777" stroke-width="1.5"/>`);
    } else if (fret === -1) {
      els.push(`<text x="${x}" y="${PAD_TOP - 6}" text-anchor="middle" fill="#555" font-size="14" font-family="sans-serif">\u00d7</text>`);
    }
  }

  if (barre != null) {
    const barreStrings = frets.map((f, i) => (f === barre ? i : -1)).filter(i => i >= 0);
    if (barreStrings.length >= 2) {
      const x1 = PAD_X + barreStrings[0] * STRING_GAP;
      const x2 = PAD_X + barreStrings[barreStrings.length - 1] * STRING_GAP;
      const cy = PAD_TOP + (barre - baseFret + 0.5) * FRET_GAP;
      els.push(`<rect x="${x1 - DOT_R}" y="${cy - DOT_R}" width="${x2 - x1 + DOT_R * 2}" height="${DOT_R * 2}" rx="${DOT_R}" fill="var(--accent, #3EDB8C)"/>`);
      els.push(`<text x="${(x1 + x2) / 2}" y="${cy + 3.5}" text-anchor="middle" fill="#fff" font-size="9" font-weight="bold" font-family="sans-serif" pointer-events="none">1</text>`);
    }
  }

  for (let s = 0; s < NUM_STRINGS; s++) {
    const fret = frets[s];
    if (fret > 0 && fret !== barre) {
      const x  = PAD_X + s * STRING_GAP;
      const cy = PAD_TOP + (fret - baseFret + 0.5) * FRET_GAP;
      els.push(`<circle cx="${x}" cy="${cy}" r="${DOT_R}" fill="var(--accent, #3EDB8C)"/>`);
      const fn = fingers ? fingers[s] : 0;
      if (fn > 0) {
        els.push(`<text x="${x}" y="${cy + 3.5}" text-anchor="middle" fill="#fff" font-size="9" font-weight="bold" font-family="sans-serif" pointer-events="none">${fn}</text>`);
      }
    }
  }

  if (baseFret > 1) {
    els.push(`<text x="${SVG_W - 1}" y="${PAD_TOP + 12}" fill="#666" font-size="10" font-family="sans-serif" text-anchor="end">${baseFret}fr</text>`);
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${SVG_W}" height="${SVG_H}" aria-label="${symbol} chord diagram">${els.join("")}</svg>`;
}

// ── Lesson lookup ─────────────────────────────────────────────────────────────
const LESSON_LOOKUP = {
  "Am":    { jg: "https://www.justinguitar.com/chords/amin",     marty: "marty+music+how+to+play+Am+chord+guitar" },
  "G":     { jg: "https://www.justinguitar.com/chords/g",        marty: "marty+music+how+to+play+G+chord+guitar" },
  "C":     { jg: "https://www.justinguitar.com/chords/c",        marty: "marty+music+how+to+play+C+chord+guitar" },
  "D":     { jg: "https://www.justinguitar.com/chords/d",        marty: "marty+music+how+to+play+D+chord+guitar" },
  "E":     { jg: "https://www.justinguitar.com/chords/e",        marty: "marty+music+how+to+play+E+chord+guitar" },
  "Em":    { jg: "https://www.justinguitar.com/chords/emin",     marty: "marty+music+how+to+play+Em+chord+guitar" },
  "F":     { jg: "https://www.justinguitar.com/chords/f",        marty: "marty+music+how+to+play+F+chord+guitar" },
  "A":     { jg: "https://www.justinguitar.com/chords/a",        marty: "marty+music+how+to+play+A+chord+guitar" },
  "Bm":    { jg: "https://www.justinguitar.com/chords/bmin",     marty: "marty+music+how+to+play+Bm+chord+guitar" },
  "C#m":   { jg: "https://www.justinguitar.com/chords/csharpm",  marty: "marty+music+how+to+play+C%23m+chord+guitar" },
  "Dm":    { jg: "https://www.justinguitar.com/chords/dmin",     marty: "marty+music+how+to+play+Dm+chord+guitar" },
  "E7":    { jg: "https://www.justinguitar.com/chords/e7",       marty: "marty+music+how+to+play+E7+chord+guitar" },
  "A7":    { jg: "https://www.justinguitar.com/chords/a7",       marty: "marty+music+how+to+play+A7+chord+guitar" },
  "D7":    { jg: "https://www.justinguitar.com/chords/d7",       marty: "marty+music+how+to+play+D7+chord+guitar" },
  "G7":    { jg: "https://www.justinguitar.com/chords/g7",       marty: "marty+music+how+to+play+G7+chord+guitar" },
  "Cadd9": { jg: "https://www.justinguitar.com/chords/c-add9-1", marty: "marty+music+how+to+play+Cadd9+chord+guitar" },
  "Dsus2": { jg: "https://www.justinguitar.com/chords/dsus2",    marty: "marty+music+how+to+play+Dsus2+chord+guitar" },
  "Esus4": { jg: "https://www.justinguitar.com/chords/esus4",    marty: "marty+music+how+to+play+Esus4+chord+guitar" },
  "Fmaj7": { jg: "https://www.justinguitar.com/chords/fmaj7",    marty: "marty+music+how+to+play+Fmaj7+chord+guitar" },
  "Cmaj7": { jg: "https://www.justinguitar.com/chords/cmaj7",    marty: "marty+music+how+to+play+Cmaj7+chord+guitar" },
  "Bb":    { jg: "https://www.justinguitar.com/guitar-lessons/easy-barre-chords-for-beginners-bg-2303", marty: "marty+music+how+to+play+Bb+chord+guitar" },
  "B7":    { jg: "https://www.justinguitar.com/chords/b7",       marty: "marty+music+how+to+play+B7+chord+guitar" },
};

/**
 * Render lesson cards for top chords that have lookup entries.
 * @param {string[]} topChords - array of chord symbols
 * @param {HTMLElement} sectionEl - the lessons section container element
 * @param {HTMLElement} cardsEl - the lesson-cards inner container
 */
function renderLessons(topChords, sectionEl, cardsEl) {
  const chords = topChords.filter(sym => LESSON_LOOKUP[sym]).slice(0, 4);
  if (chords.length === 0) { sectionEl.style.display = "none"; return; }

  cardsEl.innerHTML = chords.map(sym => {
    const { jg, marty } = LESSON_LOOKUP[sym];
    const martyUrl = `https://www.youtube.com/results?search_query=${marty}`;
    return `<div class="lesson-card">
      <div class="lesson-card-chord">${sym} chord</div>
      <div class="lesson-provider">JustinGuitar</div>
      <a class="lesson-link" href="${jg}" target="_blank" rel="noopener" onclick="if(typeof saTrack==='function')saTrack('lesson_click',{chord:'${sym}',provider:'justinguitar'})">Watch lesson &rarr;</a>
      <div class="lesson-provider">Marty Music</div>
      <a class="lesson-link" href="${martyUrl}" target="_blank" rel="noopener" onclick="if(typeof saTrack==='function')saTrack('lesson_click',{chord:'${sym}',provider:'marty_music'})">Watch lesson &rarr;</a>
    </div>`;
  }).join("");

  sectionEl.style.display = "block";
}

/**
 * Convert a key string (e.g. "A minor") to a plain-English description.
 */
function plainEnglishKey(key) {
  const lower = key.toLowerCase();
  if (lower.includes("minor")) return `The key of ${key} \u2014 gives your song a darker, more emotional feel.`;
  if (lower.includes("major")) return `The key of ${key} \u2014 bright and clear sound.`;
  return `The key of ${key}`;
}
