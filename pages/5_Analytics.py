"""Analytics dashboard page."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from lib import auth
from lib.supabase_client import get_client
from lib.srs import streak_from_reviews
from lib.utils import render_sidebar

render_sidebar("Analytics")
user = auth.current_user()
if not user:
    st.warning("Please sign in to continue.")
    st.stop()

client = get_client()

st.title("Analytics")
st.caption("Understand your learning habits and forecast upcoming reviews.")

start_date_dt = dt.date.today() - dt.timedelta(days=30)
start_date_iso = start_date_dt.isoformat()

reviews_resp = (
    client.table("reviews")
    .select("id,card_id,grade,reviewed_at,new_interval,prev_interval")
    .eq("owner", user.id)
    .gte("reviewed_at", start_date_iso)
    .order("reviewed_at")
    .execute()
)
reviews = reviews_resp.data or []

cards_resp = (
    client.table("cards")
    .select("id,deck_id,due_at,suspended")
    .eq("owner", user.id)
    .execute()
)
cards = cards_resp.data or []

decks_resp = (
    client.table("decks")
    .select("id,name")
    .eq("owner", user.id)
    .execute()
)
decks = decks_resp.data or []

deck_lookup = {deck["id"]: deck["name"] for deck in decks}
card_to_deck = {card["id"]: card.get("deck_id") for card in cards}

reviews_df = pd.DataFrame(reviews)
if not reviews_df.empty:
    reviews_df["reviewed_at"] = pd.to_datetime(reviews_df["reviewed_at"]).dt.date

st.subheader("Reviews per day (last 30 days)")
if reviews_df.empty:
    st.info("No reviews yet. Study to unlock analytics.")
else:
    per_day = reviews_df.groupby("reviewed_at").size()
    idx = pd.Index(
        pd.date_range(start=start_date_dt, end=dt.date.today()).date,
        name="date",
    )
    per_day = per_day.reindex(idx, fill_value=0)
    st.line_chart(per_day, height=250)

st.subheader("Accuracy by deck")
if reviews_df.empty:
    st.caption("Once you have reviews, deck accuracy will display here.")
else:
    deck_correct = defaultdict(int)
    deck_total = defaultdict(int)
    for _, row in reviews_df.iterrows():
        deck_id = card_to_deck.get(row["card_id"])
        if not deck_id:
            continue
        deck_total[deck_id] += 1
        if row["grade"] >= 3:
            deck_correct[deck_id] += 1
    labels = []
    accuracies = []
    for deck_id, total in deck_total.items():
        labels.append(deck_lookup.get(deck_id, "Unknown deck"))
        accuracy = deck_correct[deck_id] / total * 100 if total else 0
        accuracies.append(accuracy)
    if labels:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.bar(labels, accuracies, color="#4e79a7")
        ax.set_ylabel("Accuracy %")
        ax.set_ylim(0, 100)
        ax.tick_params(axis="x", rotation=45)
        st.pyplot(fig)
    else:
        st.caption("No deck-level review data yet.")

st.subheader("Upcoming due cards (next 14 days)")
if not cards:
    st.info("No cards available yet.")
else:
    upcoming = []
    today = dt.date.today()
    for offset in range(0, 15):
        target = today + dt.timedelta(days=offset)
        count = 0
        for card in cards:
            if card.get("suspended"):
                continue
            due_value = card.get("due_at")
            if not due_value:
                continue
            due_date = due_value if isinstance(due_value, dt.date) else dt.date.fromisoformat(str(due_value))
            if due_date == target:
                count += 1
        upcoming.append({"date": target, "due": count})
    upcoming_df = pd.DataFrame(upcoming).set_index("date")
    st.bar_chart(upcoming_df, height=250)

st.subheader("Focus stats")
col1, col2 = st.columns(2)
review_dates = (
    [row["reviewed_at"] for row in reviews_df.to_dict("records")] if not reviews_df.empty else []
)
if review_dates:
    streak = streak_from_reviews([dt.date.fromisoformat(str(day)) for day in review_dates])
else:
    streak = 0
col1.metric("Review streak", f"{streak} days")

total_reviews = len(reviews)
approx_minutes = total_reviews * 0.75
col2.metric("Estimated minutes", f"{approx_minutes:.1f} min")
