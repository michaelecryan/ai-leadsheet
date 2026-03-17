"""FastAPI backend — HTTP entry point for the ai-leadsheet pipeline.

Receives audio file uploads from the browser, runs them through the leadsheet
pipeline, and returns a chord chart as JSON. The frontend uses that JSON to
render the chart and drive playback sync.

Run locally:
    uv run uvicorn backend.main:app --reload

Environment variables
---------------------
Required:
  SUPABASE_URL              Supabase project URL
  SUPABASE_SERVICE_KEY      Supabase service role key (admin)
  STRIPE_SECRET_KEY         Stripe secret key
  STRIPE_PRICE_ID           Stripe recurring Price ID (price_...)
  STRIPE_WEBHOOK_SECRET     Stripe webhook signing secret
  RESEND_API_KEY            Resend API key (full access)
  RESEND_AUDIENCE_ID        Resend audience ID for email capture
  ANTHROPIC_API_KEY         Anthropic API key for Claude theory lessons

Optional:
  YOUTUBE_COOKIES_B64       Base64-encoded cookies.txt for yt-dlp (bypasses some bot checks)
  YT_MP3_GO_URL             yt-mp3-go fallback service URL, e.g. https://yt-mp3-go.example.com
                            API: GET {YT_MP3_GO_URL}/api/mp3?id={VIDEO_ID} → audio stream
                            Used when yt-dlp fails after retries on Railway's IP range.
  CHORD_DETECTOR            Set to "basic_pitch" to use Basic Pitch instead of librosa
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

logger = logging.getLogger("soloact")

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.auth import get_admin_client, get_current_user
from backend.stripe_routes import router as stripe_router

from leadsheet import analysis, midi
from leadsheet import simplify as simplify_mod
from leadsheet.analysis import suggest_scales
from leadsheet.theory import analyse_progression
from leadsheet.claude_lesson import generate_lesson
from leadsheet.midi import ParsedMidi

app = FastAPI(title="ai-leadsheet API", version="0.1.0")
app.include_router(stripe_router)

# Rate limiter — keyed by client IP address.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Pipeline concurrency guard — the librosa analysis pipeline is CPU/memory heavy.
# Limit simultaneous pipeline runs to avoid OOM on constrained Railway instances.
# Requests beyond this limit queue and wait rather than crashing the server.
_PIPELINE_SEMAPHORE = asyncio.Semaphore(1)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a friendly 429 instead of slowapi's default plain-text response."""
    return JSONResponse(
        status_code=429,
        content={"detail": "You've analysed a lot of songs today. Come back in an hour."},
    )


# Allow the frontend (running on a different port locally, or a different domain
# in production) to make requests to this server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://soloact.app",
        "https://www.soloact.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

class UrlRequest(BaseModel):
    """Request body for URL-based audio ingestion."""
    url: str


class UrlValidateRequest(BaseModel):
    """Request body for YouTube URL validation."""
    url: str


class SubscribeRequest(BaseModel):
    """Request body for email list subscription."""
    email: str


class SaveChartRequest(BaseModel):
    """Request body for saving a chord chart."""
    title: str
    key: str | None = None
    capo: int | None = None
    capo_hint: str | None = None
    bpm: float | None = None
    time_signature: str | None = None
    scales: list | None = None
    chords: list
    theory: dict | None = None


class UpdateChartRequest(BaseModel):
    """Request body for renaming a chart."""
    title: str


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}
_MIDI_EXTENSIONS = {".mid", ".midi"}
_ALLOWED_EXTENSIONS = _AUDIO_EXTENSIONS | _MIDI_EXTENSIONS

# NOTE: _AUDIO_EXTENSIONS is also defined in leadsheet/cli.py. Both sets should
# stay in sync. A shared constants module is the right long-term fix.


def _check_access(user_id: str) -> None:
    """Raise HTTP 402 if the user's trial has expired and they are not on a paid plan.

    Called before running the analysis pipeline so we don't burn CPU on unpaid requests.
    """
    from datetime import datetime, timezone
    client = get_admin_client()
    res = client.table("profiles").select("plan, trial_expires_at").eq("id", user_id).single().execute()
    profile = res.data or {}
    plan = profile.get("plan", "trial")
    if plan == "paid":
        return
    trial_expires_at = profile.get("trial_expires_at")
    if trial_expires_at:
        expires = datetime.fromisoformat(trial_expires_at.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) < expires:
            return
    raise HTTPException(
        status_code=402,
        detail="Your free trial has ended. Please upgrade to continue.",
    )


@app.get("/health")
def health() -> dict:
    """Health check — used by Railway and other deployment platforms to confirm the server is up."""
    return {"status": "ok"}


@app.post("/upload")
@limiter.limit("10/hour")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    authorization: str | None = None,
) -> dict:
    """Accept an audio or MIDI file, run the pipeline, and return a chord chart as JSON.

    If an Authorization header is present the user must have an active trial or paid plan.
    Anonymous requests (no token) are allowed — the 1-free-analysis gate is enforced client-side.

    Response shape:
      - key: detected key string (e.g. "E minor")
      - capo: capo fret number or null
      - capo_hint: human-readable capo instruction or null
      - scales: list of guitar-friendly scale names
      - bpm: detected tempo
      - time_signature: e.g. "4/4"
      - chords: list of {measure, symbol, time_seconds}
    """
    # If the request carries a token, enforce the paywall server-side.
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            client = get_admin_client()
            user_resp = client.auth.get_user(token)
            if user_resp.user:
                _check_access(str(user_resp.user.id))
        except HTTPException:
            raise
        except Exception:
            pass  # Invalid token — treat as anonymous, let rate limiter handle abuse
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

        # Reject files over 20 MB
        _MAX_BYTES = 20 * 1024 * 1024
        if tmp_path.stat().st_size > _MAX_BYTES:
            raise HTTPException(
                status_code=413,
                detail="File too large. Please upload an MP3 or WAV under 20MB.",
            )

        # Validate actual MIME type by reading magic bytes (guards against renamed files)
        import filetype as _filetype
        _ALLOWED_MIMES = {"audio/mpeg", "audio/wav", "audio/flac", "audio/ogg", "audio/x-m4a", "audio/midi"}
        kind = _filetype.guess(tmp_path)
        if kind is None or kind.mime not in _ALLOWED_MIMES:
            raise HTTPException(
                status_code=415,
                detail="Unsupported file type. Please upload an audio file.",
            )

        # Run the CPU-heavy pipeline off the event loop so other requests aren't blocked.
        # The semaphore caps concurrent pipeline runs to avoid OOM on constrained instances.
        async with _PIPELINE_SEMAPHORE:
            parsed, simplified = await asyncio.to_thread(_run_pipeline, tmp_path, suffix)

        key = simplified.key
        scales = suggest_scales(key)

        capo = simplified.capo
        capo_hint: str | None = None
        if capo and simplified.capo_shape_key:
            capo_hint = f"Capo {capo} and play in {simplified.capo_shape_key} shapes"

        # Convert measure number → seconds so the frontend can drive playback sync.
        # When the librosa chord detector ran, each MeasureChord carries an actual
        # beat timestamp anchored to the real audio position — use that when available.
        # Fall back to the BPM-formula for the MIDI path (MeasureChord.time_seconds is None).
        beats_per_measure = parsed.beats_per_measure
        seconds_per_beat = 60.0 / parsed.bpm

        chords = [
            {
                "measure": c.measure,
                "symbol": c.symbol,
                "time_seconds": round(
                    c.time_seconds if c.time_seconds is not None
                    else (c.measure - 1) * beats_per_measure * seconds_per_beat,
                    3,
                ),
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

    time_sig = f"{parsed.time_sig_numerator}/{parsed.time_sig_denominator}"
    theory_data = analyse_progression(key, [c["symbol"] for c in chords])
    theory_lesson = generate_lesson(
        key=key,
        unique_chords=theory_data["unique_chords"],
        roman_numerals=theory_data["roman_numerals"],
        bpm=parsed.bpm,
        time_signature=time_sig,
    )

    return {
        "status": "ok",
        "filename": file.filename,
        "key": key,
        "capo": capo,
        "capo_hint": capo_hint,
        "scales": scales,
        "bpm": round(parsed.bpm, 1),
        "time_signature": time_sig,
        "chords": chords,
        "theory": theory_lesson,
    }


# ── YouTube extraction helpers ────────────────────────────────────────────────

_YT_VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

_YT_DOWNLOAD_RETRIES = 3
_YT_RETRY_BACKOFF_S = 2


def _pick_user_agent(attempt: int) -> str:
    """Rotate through user agents deterministically by attempt number."""
    return _USER_AGENTS[attempt % len(_USER_AGENTS)]


def _extract_video_id(url: str) -> str | None:
    """Extract an 11-character YouTube video ID from any standard YouTube URL format."""
    m = _YT_VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def _ytdlp_download(url: str, out_path: Path, cookies_path: Path | None) -> dict:
    """Run yt-dlp synchronously. Returns the info dict. Raises on failure.

    Designed to be called via asyncio.to_thread — does not touch the event loop.
    """
    import yt_dlp

    attempt = 0
    last_exc: Exception | None = None

    while attempt < _YT_DOWNLOAD_RETRIES:
        ua = _pick_user_agent(attempt)
        logger.info("[yt-dlp] attempt %d/%d url=%s ua=%s", attempt + 1, _YT_DOWNLOAD_RETRIES, url, ua[:40])

        ydl_opts: dict = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": str(out_path / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 30,
            "geo_bypass": True,
            "geo_bypass_country": "IE",
            "http_headers": {"User-Agent": ua},
            # Extract to mp3 via ffmpeg postprocessor
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }],
        }

        if cookies_path is not None:
            ydl_opts["cookiefile"] = str(cookies_path)

        errors: list[str] = []

        class _ErrLogger:
            def debug(self, msg: str) -> None: pass
            def warning(self, msg: str) -> None: errors.append(f"WARN: {msg}")
            def error(self, msg: str) -> None: errors.append(f"ERR: {msg}")

        ydl_opts["logger"] = _ErrLogger()

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            logger.info("[yt-dlp] success on attempt %d", attempt + 1)
            return info
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "[yt-dlp] attempt %d failed: %s\nyt-dlp output:\n%s",
                attempt + 1, exc, "\n".join(errors) or "(none)",
            )
            attempt += 1
            if attempt < _YT_DOWNLOAD_RETRIES:
                time.sleep(_YT_RETRY_BACKOFF_S)

    raise RuntimeError(f"yt-dlp failed after {_YT_DOWNLOAD_RETRIES} attempts: {last_exc}")


def _ytmp3go_download(video_id: str, out_path: Path) -> Path:
    """Download audio via the yt-mp3-go fallback service.

    Streams the response to a temp .mp3 file. Returns the path.
    Raises if YT_MP3_GO_URL is not set or the request fails.
    """
    base_url = os.getenv("YT_MP3_GO_URL", "").rstrip("/")
    if not base_url:
        raise RuntimeError("YT_MP3_GO_URL not configured — no fallback available")

    api_url = f"{base_url}/api/mp3?id={video_id}"
    logger.info("[yt-mp3-go] fetching %s", api_url)

    dest = out_path / f"{uuid.uuid4().hex}.mp3"
    req = urllib.request.Request(api_url, headers={"User-Agent": _USER_AGENTS[0]})
    with urllib.request.urlopen(req, timeout=90) as resp:
        if resp.status != 200:
            raise RuntimeError(f"yt-mp3-go returned HTTP {resp.status}")
        dest.write_bytes(resp.read())

    logger.info("[yt-mp3-go] downloaded %d bytes to %s", dest.stat().st_size, dest.name)
    return dest


@app.post("/upload-url")
async def upload_url(req: UrlRequest) -> dict:
    """Download audio from a YouTube URL, run the pipeline, and return a chord chart.

    Extraction strategy (in order):
    1. yt-dlp with hardened config (user-agent rotation, geo-bypass, 3 retries)
    2. yt-mp3-go fallback service (if YT_MP3_GO_URL env var is set)
    3. Clear error message if both fail

    Returns the same JSON shape as /upload, plus video_id and title for the
    frontend YouTube embed/playback sync.
    """
    from urllib.parse import urlparse as _urlparse
    import base64

    _ALLOWED_URL_HOSTS = {"www.youtube.com", "youtube.com", "youtu.be", "m.youtube.com"}
    _parsed_url = _urlparse(req.url)
    if _parsed_url.hostname not in _ALLOWED_URL_HOSTS:
        raise HTTPException(status_code=400, detail="Only YouTube URLs are supported.")

    video_id = _extract_video_id(req.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Could not parse a YouTube video ID from that URL.")

    tmp_dir_obj = tempfile.TemporaryDirectory()
    tmp_dir = Path(tmp_dir_obj.name)
    audio_path: Path | None = None
    title = "YouTube track"

    try:
        # Write cookies file once (shared across yt-dlp attempts)
        cookies_path: Path | None = None
        cookies_b64 = os.getenv("YOUTUBE_COOKIES_B64")
        if cookies_b64:
            cookies_path = tmp_dir / "cookies.txt"
            cookies_path.write_bytes(base64.b64decode(cookies_b64))

        # ── Attempt 1: yt-dlp ────────────────────────────────────────────────
        ytdlp_ok = False
        try:
            info = await asyncio.to_thread(_ytdlp_download, req.url, tmp_dir, cookies_path)
            title = info.get("title", "YouTube track")
            # After FFmpegExtractAudio, file is <id>.mp3
            mp3_path = tmp_dir / f"{video_id}.mp3"
            if mp3_path.exists():
                audio_path = mp3_path
            else:
                # Fallback: find any audio file in tmp_dir
                candidates = [f for f in tmp_dir.iterdir() if f.suffix.lower() in _AUDIO_EXTENSIONS]
                if candidates:
                    audio_path = candidates[0]
            if audio_path:
                ytdlp_ok = True
            else:
                logger.warning("[yt-dlp] no audio file found after extraction")
        except Exception as exc:
            logger.warning("[yt-dlp] all retries exhausted: %s", exc)

        # ── Attempt 2: yt-mp3-go fallback ───────────────────────────────────
        if not ytdlp_ok:
            logger.info("[upload-url] falling back to yt-mp3-go for video_id=%s", video_id)
            try:
                audio_path = await asyncio.to_thread(_ytmp3go_download, video_id, tmp_dir)
            except Exception as exc:
                logger.error("[yt-mp3-go] fallback also failed: %s", exc)
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Could not extract audio from this YouTube video. "
                        "This is usually a temporary issue — try again in a few minutes."
                    ),
                ) from exc

        suffix = audio_path.suffix.lower()

        async with _PIPELINE_SEMAPHORE:
            parsed, simplified = await asyncio.to_thread(_run_pipeline, audio_path, suffix)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Download error: {exc}") from exc
    finally:
        tmp_dir_obj.cleanup()

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
            "time_seconds": round(
                c.time_seconds if c.time_seconds is not None
                else (c.measure - 1) * beats_per_measure * seconds_per_beat,
                3,
            ),
        }
        for c in simplified.chords
    ]
    time_sig = f"{parsed.time_sig_numerator}/{parsed.time_sig_denominator}"
    theory_data = analyse_progression(key, [c["symbol"] for c in chords])
    theory_lesson = generate_lesson(
        key=key,
        unique_chords=theory_data["unique_chords"],
        roman_numerals=theory_data["roman_numerals"],
        bpm=parsed.bpm,
        time_signature=time_sig,
    )

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
        "time_signature": time_sig,
        "chords": chords,
        "theory": theory_lesson,
    }


@app.post("/api/youtube/validate")
async def youtube_validate(req: UrlValidateRequest) -> dict:
    """Check whether a YouTube URL points to a real, accessible video.

    Uses the YouTube oEmbed API (no API key required) — lightweight, no
    audio extraction. Called by the frontend on URL paste/blur so the user
    gets immediate feedback before hitting Submit.

    Returns:
        { valid: true,  title: str, thumbnail: str }
        { valid: false, error: str }
    """
    video_id = _extract_video_id(req.url)
    if not video_id:
        return {"valid": False, "error": "Not a recognised YouTube URL."}

    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        oembed_req = urllib.request.Request(
            oembed_url,
            headers={"User-Agent": _USER_AGENTS[0]},
        )
        with urllib.request.urlopen(oembed_req, timeout=8) as resp:
            data = json.loads(resp.read())
        return {
            "valid": True,
            "title": data.get("title", ""),
            "thumbnail": data.get("thumbnail_url", ""),
        }
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"valid": False, "error": "Video not found or is private."}
        return {"valid": False, "error": f"YouTube returned an error ({exc.code})."}
    except Exception as exc:
        logger.warning("[youtube/validate] oEmbed failed: %s", exc)
        return {"valid": False, "error": "Could not reach YouTube to validate this URL."}


@app.post("/api/subscribe")
async def subscribe(req: SubscribeRequest) -> dict:
    """Add an email address to a Resend Audience.

    Validates the email format, then either:
    - Posts to the Resend Contacts API if RESEND_API_KEY + RESEND_AUDIENCE_ID are set
    - Logs the email to stdout and returns success (dev / missing keys)
    """
    if not _EMAIL_RE.match(req.email):
        raise HTTPException(status_code=400, detail="Invalid email address.")

    api_key     = os.getenv("RESEND_API_KEY")
    audience_id = os.getenv("RESEND_AUDIENCE_ID")
    if not api_key or not audience_id:
        print(f"[subscribe] RESEND_API_KEY/RESEND_AUDIENCE_ID not set — would have subscribed: {req.email}")
        return {"success": True}

    import resend as resend_sdk
    resend_sdk.api_key = api_key
    try:
        resend_sdk.Contacts.create({
            "email": req.email,
            "unsubscribed": False,
            "audience_id": audience_id,
        })
        print(f"[subscribe] Resend contact created for {req.email}")
    except resend_sdk.exceptions.ResendError as exc:
        print(f"[subscribe] Resend error {exc}: {exc}")
        # Already exists — treat as success
        if "already exists" in str(exc).lower() or getattr(exc, "status_code", 0) == 422:
            return {"success": True}
        raise HTTPException(status_code=500, detail="Subscription service error.") from exc
    except Exception as exc:
        print(f"[subscribe] Unexpected error: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Subscription service error.") from exc

    return {"success": True}


@app.get("/api/profile")
async def get_profile(user=Depends(get_current_user)) -> dict:
    """Return the authenticated user's profile (trial expiry, analysis count)."""
    client = get_admin_client()
    result = client.table("profiles").select("*").eq("id", str(user.id)).execute()
    if not result.data:
        return {"profile": None}
    return {"profile": result.data[0]}


@app.post("/api/charts")
async def save_chart(req: SaveChartRequest, user=Depends(get_current_user)) -> dict:
    """Save a chord chart for the authenticated user. Returns the saved chart row."""
    client = get_admin_client()
    result = client.table("charts").insert({
        "user_id": str(user.id),
        "title": req.title,
        "key": req.key,
        "capo": req.capo,
        "capo_hint": req.capo_hint,
        "bpm": int(req.bpm) if req.bpm is not None else None,
        "time_signature": req.time_signature,
        "scales": req.scales,
        "chords": req.chords,
        "theory": req.theory,
    }).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save chart.")
    return {"chart": result.data[0]}


@app.get("/api/charts")
async def list_charts(user=Depends(get_current_user)) -> dict:
    """Return all saved charts for the authenticated user, newest first."""
    client = get_admin_client()
    result = (
        client.table("charts")
        .select("id, title, key, capo, bpm, time_signature, created_at")
        .eq("user_id", str(user.id))
        .order("created_at", desc=True)
        .execute()
    )
    return {"charts": result.data}


@app.get("/api/charts/{chart_id}")
async def get_chart(chart_id: str, user=Depends(get_current_user)) -> dict:
    """Return a single chart by ID. Returns 404 if it doesn't belong to the user."""
    client = get_admin_client()
    result = (
        client.table("charts")
        .select("*")
        .eq("id", chart_id)
        .eq("user_id", str(user.id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Chart not found.")
    return {"chart": result.data[0]}


@app.get("/api/charts/{chart_id}/public")
async def get_chart_public(chart_id: str) -> dict:
    """Return a single chart by ID without authentication.

    Used for shared chart links so recipients can view without signing up.
    Does not require auth — only returns chart data, no owner actions.
    """
    client = get_admin_client()
    result = (
        client.table("charts")
        .select("*")
        .eq("id", chart_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Chart not found.")
    chart = result.data[0]
    # Strip owner-sensitive fields
    chart.pop("user_id", None)
    return {"chart": chart}


@app.patch("/api/charts/{chart_id}")
async def rename_chart(chart_id: str, req: UpdateChartRequest, user=Depends(get_current_user)) -> dict:
    """Rename a chart. Returns 404 if the chart doesn't belong to the user."""
    client = get_admin_client()
    result = (
        client.table("charts")
        .update({"title": req.title})
        .eq("id", chart_id)
        .eq("user_id", str(user.id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Chart not found.")
    return {"chart": result.data[0]}


@app.delete("/api/charts/{chart_id}")
async def delete_chart(chart_id: str, user=Depends(get_current_user)) -> dict:
    """Delete a chart. Returns 404 if the chart doesn't belong to the user."""
    client = get_admin_client()
    result = (
        client.table("charts")
        .delete()
        .eq("id", chart_id)
        .eq("user_id", str(user.id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Chart not found.")
    return {"success": True}


@app.get("/dashboard")
def dashboard() -> FileResponse:
    """Serve the saved charts dashboard."""
    return FileResponse("frontend/dashboard.html")


@app.get("/chart/{chart_id}")
def chart_view(chart_id: str) -> FileResponse:
    """Serve the individual chart view page (chart ID read client-side from URL)."""
    return FileResponse("frontend/chart.html")


@app.get("/example")
def example_page() -> RedirectResponse:
    """Redirect to the main page with example query param.

    Serves the standard index.html which detects ?example=1 and
    auto-renders a pre-built chart with working audio playback.
    TODO: Replace /static/example.mp3 with a real Suno track
    (Am G F C, A minor, ~122 BPM) before going live.
    """
    return RedirectResponse(url="/?example=1", status_code=302)


@app.get("/settings")
def settings_page() -> FileResponse:
    """Serve the account settings page."""
    return FileResponse("frontend/settings.html")


@app.get("/privacy")
def privacy_policy() -> FileResponse:
    """Serve the privacy policy page."""
    return FileResponse("frontend/privacy.html")


@app.get("/terms")
def terms_of_use() -> FileResponse:
    """Serve the terms of use page."""
    return FileResponse("frontend/terms.html")


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
