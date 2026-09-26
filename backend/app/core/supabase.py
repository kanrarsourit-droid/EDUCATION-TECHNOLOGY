"""
Supabase client initialization module.

Provides a configured Supabase client instance and helper methods
to safely access the Supabase service.
"""

from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Returns an initialized Supabase Client instance.
    Raises RuntimeError if required configuration is missing or invalid.
    """
    global _client
    if _client is not None:
        return _client

    url = (settings.SUPABASE_URL or "").strip()
    key = (settings.SUPABASE_SECRET_KEY or "").strip()

    if not url:
        raise RuntimeError("SUPABASE_URL is not set. Please set it in backend/.env")

    if not key:
        raise RuntimeError("SUPABASE_SECRET_KEY is not set. Please set it in backend/.env")

    if not url or "your-supabase" in url:
        raise RuntimeError("SUPABASE_URL is not set. Please set it in backend/.env")

    if not key or key == "your-supabase-secret-key":
        raise RuntimeError("SUPABASE_SECRET_KEY is not set. Please set it in backend/.env")

    _client = create_client(url, key)
    return _client


class _SupabaseClientProxy:
    """Lazy proxy allowing direct access to the client while deferring initialization."""

    def __getattr__(self, name: str):
        return getattr(get_supabase_client(), name)


# Expose client instance for convenience
supabase: Client = _SupabaseClientProxy()  # type: ignore
