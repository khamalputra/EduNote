"""Utility helpers for CSV operations, tag management, and dates."""
from __future__ import annotations

import datetime as dt
import io
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
import streamlit as st

NAV_PAGES = [
    ("Dashboard", "pages/1_Dashboard.py"),
    ("Notes", "pages/2_Notes.py"),
    ("Decks & Cards", "pages/3_Decks_and_Cards.py"),
    ("Study", "pages/4_Study.py"),
    ("Analytics", "pages/5_Analytics.py"),
    ("Settings", "pages/6_Settings.py"),
]


def render_sidebar(active: str, *, show_nav: bool = True) -> None:
    """Render the global navigation in the sidebar."""
    with st.sidebar:
        logo_path = Path("assets/logo.png")
        if logo_path.exists():
            try:
                st.image(str(logo_path), width=140)
            except Exception:
                st.markdown("### EduNote")
        else:
            st.markdown("### EduNote")
        st.markdown("## EduNote")
        if show_nav:
            for label, page in NAV_PAGES:
                if st.button(label, use_container_width=True, key=f"nav-{label}"):
                    st.switch_page(page)
                if label == active:
                    st.caption("Currently viewing")


def parse_tags(raw: str) -> List[str]:
    """Parse a comma-separated tag string into a list."""
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def tags_to_string(tags: Iterable[str]) -> str:
    """Join tags back to a comma separated representation."""
    return ", ".join(sorted(set(tag for tag in tags if tag)))


def dataframe_to_csv(df: pd.DataFrame) -> bytes:
    """Serialize a dataframe to CSV bytes using UTF-8 encoding."""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def read_uploaded_csv(file) -> pd.DataFrame:
    """Read an uploaded CSV file-like object into a DataFrame."""
    return pd.read_csv(file)


def to_date(value: Optional[str]) -> Optional[dt.date]:
    """Convert a string timestamp to a date object."""
    if not value:
        return None
    return dt.datetime.fromisoformat(str(value)).date()
