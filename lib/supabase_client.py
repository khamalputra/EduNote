"""Supabase client singleton used across the application."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client


@lru_cache(maxsize=1)
def _load_env() -> None:
    """Load environment variables from .env if present."""
    load_dotenv()


def _create_supabase_client() -> Client:
    """Instantiate a Supabase client using environment variables."""
    _load_env()
    url: Optional[str] = os.getenv("SUPABASE_URL")
    anon_key: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    if not url or not anon_key:
        raise RuntimeError(
            "Missing Supabase configuration. Set SUPABASE_URL and SUPABASE_ANON_KEY."
        )
    return create_client(url, anon_key)


_client: Optional[Client] = None


def get_client() -> Client:
    """Return a shared Supabase client instance."""
    global _client
    if _client is None:
        _client = _create_supabase_client()
    return _client
