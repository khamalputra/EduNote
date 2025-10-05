"""Study session page implementing SM-2 reviews."""
from __future__ import annotations

import datetime as dt

import streamlit as st

from lib import auth
from lib.supabase_client import get_client
from lib.utils import render_sidebar

render_sidebar("Study")
user = auth.current_user()
if not user:
    st.warning("Please sign in to continue.")
    st.stop()

client = get_client()

st.title("Study session")
st.caption("Review due flashcards using spaced repetition.")

if "study_stats" not in st.session_state:
    st.session_state["study_stats"] = {"reviews": 0, "correct": 0}


def load_next_card() -> None:
    """Fetch and set the next due card."""
    today = dt.date.today().isoformat()
    response = (
        client.table("cards")
        .select("id,front,back,due_at,interval_days,ease,reps,lapses")
        .eq("owner", user.id)
        .eq("suspended", False)
        .lte("due_at", today)
        .order("due_at")
        .limit(1)
        .execute()
    )
    cards = response.data or []
    st.session_state["study_card"] = cards[0] if cards else None
    st.session_state["study_revealed"] = False


def show_back_and_grade(card: dict) -> None:
    """Render the back of the card with grading controls."""
    st.info(card["back"])
    st.write("How well did you recall this card?")
    cols = st.columns(6)
    for grade in range(6):
        if cols[grade].button(str(grade), key=f"grade-{grade}"):
            client.rpc("apply_review", {"p_card": card["id"], "p_grade": grade}).execute()
            stats = st.session_state["study_stats"]
            stats["reviews"] += 1
            if grade >= 3:
                stats["correct"] += 1
            load_next_card()
            st.experimental_rerun()


if "study_card" not in st.session_state:
    load_next_card()

current = st.session_state.get("study_card")

if not current:
    st.success("All caught up! No cards due right now.")
    stats = st.session_state["study_stats"]
    if stats["reviews"]:
        accuracy = stats["correct"] / stats["reviews"] * 100
        st.metric("Session accuracy", f"{accuracy:.0f}%", help="Grades 3-5 count as correct")
        st.metric("Cards reviewed", stats["reviews"])
    st.stop()

st.subheader("Current card")
st.write(current["front"])

if not st.session_state.get("study_revealed", False):
    if st.button("Reveal", type="primary", use_container_width=True):
        st.session_state["study_revealed"] = True
        st.experimental_rerun()

if st.session_state.get("study_revealed", False):
    show_back_and_grade(current)

st.caption(
    "Grades: 0=Null, 1=Incorrect, 2=Hard, 3=Good, 4=Easy, 5=Perfect recall"
)
