"""FastAPI backend — HTTP entry point for the ai-leadsheet pipeline.

Receives audio file uploads from the browser, runs them through the leadsheet
pipeline, and returns a chord chart as JSON. The frontend uses that JSON to
render the chart and drive playback sync.

Run locally:
    uv run uvicorn backend.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ai-leadsheet API", version="0.1.0")

# Allow the frontend (running on a different port locally, or a different domain
# in production) to make requests to this server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this when deploying to production
    allow_methods=["*"],
    allow_headers=["*"],
)

_ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".mid", ".midi"}


@app.get("/health")
def health() -> dict:
    """Health check — used by Railway and other deployment platforms to confirm the server is up."""
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    """Accept an audio or MIDI file and return a placeholder chord chart response.

    This endpoint will be wired to the full pipeline in issue #4. For now it
    validates the file type and returns a stub so the frontend can be built
    against a real API contract.
    """
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{suffix}'. Accepted: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
        )

    # Placeholder response — real pipeline wired in issue #4
    return {
        "status": "ok",
        "filename": file.filename,
        "key": "E minor",
        "capo": None,
        "scales": ["E minor pentatonic", "E natural minor"],
        "chords": [
            {"measure": 1, "symbol": "Em"},
            {"measure": 2, "symbol": "G"},
            {"measure": 3, "symbol": "D"},
            {"measure": 4, "symbol": "C"},
        ],
    }
