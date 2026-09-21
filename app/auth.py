from fastapi import Header, HTTPException

from app.supabase_client import supabase


def get_current_user(authorization: str | None = Header(default=None)):
    """Validate a Supabase access token and return the authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        response = supabase.auth.get_user(token)
        user = response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user
