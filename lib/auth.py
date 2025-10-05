"""Authentication helpers that wrap Supabase Auth."""
from __future__ import annotations

from typing import Optional, Tuple

import streamlit as st
from supabase import Client
from supabase.lib.auth_client import SupabaseAuthException

from .supabase_client import get_client


def _client() -> Client:
    return get_client()


def sign_in(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """Sign in a user with email/password."""
    try:
        response = _client().auth.sign_in_with_password({"email": email, "password": password})
        user = response.user
        if user is None:
            return False, "Invalid credentials"
        st.session_state["user"] = user
        return True, None
    except SupabaseAuthException as exc:
        return False, str(exc)


def sign_up(email: str, password: str, full_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Register a new user and optionally set profile metadata."""
    try:
        response = _client().auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"full_name": full_name} if full_name else {}},
            }
        )
        user = response.user
        if user:
            st.session_state["user"] = user
            return True, None
        return False, "Unable to register user"
    except SupabaseAuthException as exc:
        return False, str(exc)


def sign_out() -> None:
    """Invalidate the current session."""
    _client().auth.sign_out()
    st.session_state.pop("user", None)


def current_user() -> Optional[dict]:
    """Return the current authenticated user."""
    if "user" in st.session_state and st.session_state["user"]:
        return st.session_state["user"]
    response = _client().auth.get_user()
    user = response.user
    if user:
        st.session_state["user"] = user
        return user
    return None
