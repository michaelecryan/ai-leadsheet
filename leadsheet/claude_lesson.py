"""Generate a beginner-friendly music theory micro-lesson via the Claude API.

Accepts structured song data (key, Roman numeral progression, tempo, time signature)
and returns a 4-field JSON lesson anchored to the specific uploaded song.

Returns None if ANTHROPIC_API_KEY is not set or the API call fails, so the rest
of the pipeline is never blocked by this layer.
"""

from __future__ import annotations

import json
import os


_SYSTEM_PROMPT = (
    "You are a music teacher writing for a complete beginner who has just uploaded "
    "their AI-generated song to a guitar learning app. They can see the chord diagrams "
    "and are about to try playing their song for the first time. Write like a "
    "knowledgeable friend — encouraging, specific, never condescending."
)

_USER_TEMPLATE = """\
Song data:
- Key: {key}
- Chord progression (unique chords in order of first appearance): {progression}
- Tempo: {bpm} BPM
- Time signature: {time_signature}

Write a micro-lesson as a JSON object with exactly these fields:
- "progression_summary": one sentence describing the chord movement in plain English, \
including the Roman numeral sequence (e.g. vi–IV–I–V)
- "emotional_character": one to two sentences on why this progression sounds the way it does
- "beginner_takeaway": one actionable sentence — something the person can actually do tonight
- "theory_note": one sentence on something genuinely interesting (modal flavour, borrowed \
chord, why this progression appears in hundreds of songs) — omit this field entirely if \
there is nothing notable; do not pad

Rules:
- Never speculate beyond what the chord data confirms
- All included fields: maximum 2 sentences each
- Respond with only the JSON object, no markdown fences, no other text
"""


def generate_lesson(
    key: str,
    unique_chords: list[str],
    roman_numerals: list[str],
    bpm: float,
    time_signature: str,
) -> dict[str, str] | None:
    """Call Claude to produce a beginner music theory micro-lesson.

    Returns a dict with keys: progression_summary, emotional_character,
    beginner_takeaway, and optionally theory_note.
    Returns None if ANTHROPIC_API_KEY is not set or the call fails.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        progression = " – ".join(
            f"{sym} ({roman})" for sym, roman in zip(unique_chords, roman_numerals)
        )

        user_msg = _USER_TEMPLATE.format(
            key=key,
            progression=progression,
            bpm=round(bpm),
            time_signature=time_signature,
        )

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )

        raw = message.content[0].text.strip()
        # Strip markdown code fences in case the model wraps output anyway
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        lesson: dict = json.loads(raw)

        # Require at least the two core fields
        if "progression_summary" not in lesson or "emotional_character" not in lesson:
            return None

        return lesson

    except Exception:
        return None
