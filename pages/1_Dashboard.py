"""Dashboard overview page."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from lib import auth
from lib.supabase_client import get_client
from lib.utils import render_sidebar

render_sidebar("Dashboard")
user = auth.current_user()
if not user:
    st.warning("Please sign in to continue.")
    st.stop()

client = get_client()

st.title("Dashboard")
st.caption("Your learning hub at a glance")

today = dt.date.today().isoformat()
due_response = (
    client.table("cards")
    .select("id", count="exact")
    .eq("owner", user.id)
    .lte("due_at", today)
    .eq("suspended", False)
    .execute()
)
due_today = due_response.count or 0

notes_count_resp = (
    client.table("notes")
    .select("id", count="exact")
    .eq("owner", user.id)
    .execute()
)
notes_total = notes_count_resp.count or 0

decks_count_resp = (
    client.table("decks")
    .select("id", count="exact")
    .eq("owner", user.id)
    .execute()
)
decks_total = decks_count_resp.count or 0

col1, col2, col3 = st.columns(3)
col1.metric("Cards due today", due_today)
col2.metric("Total notes", notes_total)
col3.metric("Total decks", decks_total)

notes_response = (
    client.table("notes")
    .select("id,title,updated_at")
    .eq("owner", user.id)
    .order("updated_at", desc=True)
    .limit(5)
    .execute()
)
notes_data = notes_response.data or []

if notes_data:
    notes_df = pd.DataFrame(notes_data)
    notes_df["updated_at"] = pd.to_datetime(notes_df["updated_at"])
    st.subheader("Recent notes")
    st.dataframe(notes_df[["title", "updated_at"]].rename(columns={"updated_at": "Last updated"}), use_container_width=True)
else:
    st.info("No notes yet. Create your first note to get started.")

st.subheader("Quick actions")
a1, a2, a3 = st.columns(3)
if a1.button("➕ New Note", use_container_width=True):
    st.switch_page("pages/2_Notes.py")
if a2.button("🗂️ New Deck", use_container_width=True):
    st.switch_page("pages/3_Decks_and_Cards.py")
if a3.button("▶️ Start Review", use_container_width=True):
    st.switch_page("pages/4_Study.py")
