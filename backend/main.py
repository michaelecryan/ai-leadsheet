"""FastAPI backend — HTTP entry point for the ai-leadsheet pipeline.

Receives audio file uploads from the browser, runs them through the leadsheet
pipeline, and returns a chord chart as JSON. The frontend uses that JSON to
render the chart and drive playback sync.

Run locally:
    uv run uvicorn backend.main:app --reload
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from leadsheet import analysis, midi
from leadsheet import simplify as simplify_mod
from leadsheet.analysis import suggest_scales
from leadsheet.midi import ParsedMidi

app = FastAPI(title="ai-leadsheet API", version="0.1.0")

# Allow the frontend (running on a different port locally, or a different domain
# in production) to make requests to this server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this when deploying to production
    allow_methods=["*"],
    allow_headers=["*"],
)

class UrlRequest(BaseModel):
    """Request body for URL-based audio ingestion."""
    url: str


_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}
_MIDI_EXTENSIONS = {".mid", ".midi"}
_ALLOWED_EXTENSIONS = _AUDIO_EXTENSIONS | _MIDI_EXTENSIONS

# NOTE: _AUDIO_EXTENSIONS is also defined in leadsheet/cli.py. Both sets should
# stay in sync. A shared constants module is the right long-term fix.


@app.get("/health")
def health() -> dict:
    """Health check — used by Railway and other deployment platforms to confirm the server is up."""
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    """Accept an audio or MIDI file, run the pipeline, and return a chord chart as JSON.

    Response shape:
      - key: detected key string (e.g. "E minor")
      - capo: capo fret number or null
      - capo_hint: human-readable capo instruction or null
      - scales: list of guitar-friendly scale names
      - bpm: detected tempo
      - time_signature: e.g. "4/4"
      - chords: list of {measure, symbol, time_seconds}
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{suffix}'. Accepted: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
        )

    # Stream upload to a temp file in 1 MB chunks (avoids loading large audio into memory at once)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            while chunk := await file.read(1024 * 1024):
                tmp.write(chunk)
            tmp_path = Path(tmp.name)

        # Run the CPU-heavy pipeline off the event loop so other requests aren't blocked
        parsed, simplified = await asyncio.to_thread(_run_pipeline, tmp_path, suffix)

        key = simplified.key
        scales = suggest_scales(key)

        capo = simplified.capo
        capo_hint: str | None = None
        if capo and simplified.capo_shape_key:
            capo_hint = f"Capo {capo} and play in {simplified.capo_shape_key} shapes"

        # Convert measure number → seconds so the frontend can drive playback sync
        beats_per_measure = parsed.beats_per_measure
        seconds_per_beat = 60.0 / parsed.bpm

        chords = [
            {
                "measure": c.measure,
                "symbol": c.symbol,
                # Time in seconds when this chord starts in the audio
                "time_seconds": round((c.measure - 1) * beats_per_measure * seconds_per_beat, 3),
            }
            for c in simplified.chords
        ]

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}") from exc
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)

    return {
        "status": "ok",
        "filename": file.filename,
        "key": key,
        "capo": capo,
        "capo_hint": capo_hint,
        "scales": scales,
        "bpm": round(parsed.bpm, 1),
        "time_signature": f"{parsed.time_sig_numerator}/{parsed.time_sig_denominator}",
        "chords": chords,
    }


@app.post("/upload-url")
async def upload_url(req: UrlRequest) -> dict:
    """Download audio from a YouTube URL, run the pipeline, and return a chord chart.

    Uses yt-dlp to fetch the best available audio stream, converts to MP3, then
    passes through the same librosa pipeline as a file upload. Returns the same
    JSON shape as /upload, plus video_id and title for the frontend YouTube embed.
    """
    import yt_dlp

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ydl_opts = {
                # Prefer m4a (no ffmpeg needed); fall back to any audio
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "outtmpl": str(Path(tmp_dir) / "%(id)s.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(req.url, download=True)

            video_id = info.get("id", "")
            title = info.get("title", "YouTube track")

            # Find whichever audio file yt-dlp downloaded
            audio_files = [
                f for f in Path(tmp_dir).iterdir()
                if f.suffix.lower() in _AUDIO_EXTENSIONS
            ]
            if not audio_files:
                raise ValueError("No supported audio file found after download")
            audio_path = audio_files[0]
            suffix = audio_path.suffix.lower()

            parsed, simplified = await asyncio.to_thread(_run_pipeline, audio_path, suffix)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Download error: {exc}") from exc

    key = simplified.key
    scales = suggest_scales(key)
    capo = simplified.capo
    capo_hint: str | None = None
    if capo and simplified.capo_shape_key:
        capo_hint = f"Capo {capo} and play in {simplified.capo_shape_key} shapes"
    beats_per_measure = parsed.beats_per_measure
    seconds_per_beat = 60.0 / parsed.bpm
    chords = [
        {
            "measure": c.measure,
            "symbol": c.symbol,
            "time_seconds": round((c.measure - 1) * beats_per_measure * seconds_per_beat, 3),
        }
        for c in simplified.chords
    ]
    return {
        "status": "ok",
        "filename": title,
        "video_id": video_id,
        "title": title,
        "key": key,
        "capo": capo,
        "capo_hint": capo_hint,
        "scales": scales,
        "bpm": round(parsed.bpm, 1),
        "time_signature": f"{parsed.time_sig_numerator}/{parsed.time_sig_denominator}",
        "chords": chords,
    }


# Serve the frontend — must be mounted after all API routes so they are not shadowed.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


def _run_pipeline(tmp_path: Path, suffix: str) -> tuple[ParsedMidi, object]:
    """Load, analyse, and simplify an audio or MIDI file.

    Runs synchronously — call via asyncio.to_thread() from async endpoints
    so the event loop is not blocked during CPU-heavy transcription.

    Default audio path: librosa beat-synchronous chromagram chord detection.
    Set CHORD_DETECTOR=basic_pitch to fall back to Basic Pitch transcription.
    """
    if suffix in _AUDIO_EXTENSIONS:
        if os.getenv("CHORD_DETECTOR") == "basic_pitch":
            # Fallback: Basic Pitch neural transcription (note-level, slower)
            from leadsheet import audio as audio_mod  # lazy import (heavy deps)
            parsed = audio_mod.load_audio(tmp_path)
            result = analysis.analyse(parsed)
        else:
            # Default: librosa chromagram (chord-level, faster, better accuracy)
            from leadsheet.chord_detector import detect_chords_librosa
            parsed, result = detect_chords_librosa(tmp_path)
    else:
        parsed = midi.load(tmp_path)
        result = analysis.analyse(parsed)

    simplified = simplify_mod.simplify(result)
    return parsed, simplified
