"""Auth helpers — Supabase JWT verification for FastAPI endpoints.

Provides a FastAPI dependency (get_current_user) that validates a Bearer token
from the Authorization header and returns the authenticated Supabase user.

Usage in a route:
    from backend.auth import get_current_user
    from fastapi import Depends

    @app.get("/api/protected")
    async def protected(user=Depends(get_current_user)):
        return {"user_id": user.id}
"""

from __future__ import annotations

import os

from fastapi import Header, HTTPException
from supabase import Client, create_client

# Module-level admin client — initialised once on first use.
_admin_client: Client | None = None


def get_admin_client() -> Client:
    """Return (or lazily create) the Supabase admin client.

    Uses the service role key, which bypasses Row Level Security.
    All routes that call this must enforce ownership checks manually.
    """
    global _admin_client
    if _admin_client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables must be set."
            )
        _admin_client = create_client(url, key)
    return _admin_client


async def get_current_user(authorization: str = Header(None, alias="Authorization")):
    """FastAPI dependency — validates a Supabase Bearer token and returns the user.

    Raises HTTP 401 if the header is missing, malformed, or the token is invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token = authorization[7:]  # strip "Bearer "
    try:
        client = get_admin_client()
        response = client.auth.get_user(token)
        if response.user is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        return response.user
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from exc
