"""Notes management page."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth
from lib.supabase_client import get_client
from lib.utils import parse_tags, render_sidebar, tags_to_string

render_sidebar("Notes")
user = auth.current_user()
if not user:
    st.warning("Please sign in to continue.")
    st.stop()

client = get_client()

st.title("Notes")
st.caption("Write, search, and convert notes into flashcards.")

notes_resp = (
    client.table("notes")
    .select("id,title,body_markdown,tags,created_at,updated_at")
    .eq("owner", user.id)
    .order("updated_at", desc=True)
    .execute()
)
notes = notes_resp.data or []

all_tags = sorted({tag for note in notes for tag in (note.get("tags") or []) if tag})

search = st.text_input("Search notes", placeholder="Title or body")
tag_filter = st.multiselect("Filter by tags", options=all_tags)

filtered_notes = []
for note in notes:
    haystack = f"{note.get('title', '')} {note.get('body_markdown', '')}".lower()
    matches_search = search.lower() in haystack if search else True
    note_tags = note.get("tags") or []
    matches_tags = set(tag_filter).issubset(set(note_tags)) if tag_filter else True
    if matches_search and matches_tags:
        filtered_notes.append(note)

if filtered_notes:
    notes_df = pd.DataFrame(filtered_notes)
    notes_df["updated_at"] = pd.to_datetime(notes_df["updated_at"])
    st.dataframe(
        notes_df[["title", "tags", "updated_at"]].rename(columns={"updated_at": "Last updated"}),
        use_container_width=True,
    )
else:
    st.info("No notes match your filters yet.")

options = [("➕ New note", None)] + [
    (f"{note['title']} ({note['id'][:8]})", note) for note in notes
]
labels = [label for label, _ in options]
selected_label = st.selectbox("Select a note to edit", options=labels)
selected_note = next(note for label, note in options if label == selected_label)

with st.form("note-form"):
    title = st.text_input("Title", value=selected_note["title"] if selected_note else "")
    body = st.text_area(
        "Markdown body",
        value=selected_note["body_markdown"] if selected_note else "",
        height=300,
    )
    tags_str = st.text_input(
        "Tags (comma separated)",
        value=tags_to_string(selected_note.get("tags", [])) if selected_note else "",
    )
    submitted = st.form_submit_button("Save note", use_container_width=True)

    if submitted:
        payload = {
            "title": title.strip(),
            "body_markdown": body,
            "tags": parse_tags(tags_str),
            "owner": user.id,
        }
        if not payload["title"]:
            st.error("Title is required.")
        else:
            if selected_note:
                update_payload = payload.copy()
                update_payload.pop("owner", None)
                client.table("notes").update(update_payload).eq("id", selected_note["id"]).execute()
                st.success("Note updated.")
            else:
                client.table("notes").insert(payload).execute()
                st.success("Note created.")
            st.experimental_rerun()

if selected_note:
    with st.expander("Convert note to flashcards"):
        decks_resp = (
            client.table("decks")
            .select("id,name")
            .eq("owner", user.id)
            .order("name")
            .execute()
        )
        decks = decks_resp.data or []
        if not decks:
            st.info("Create a deck first before adding cards.")
        else:
            deck_options = {deck["name"]: deck["id"] for deck in decks}
            deck_label = st.selectbox("Target deck", options=list(deck_options.keys()))
            deck_id = deck_options[deck_label]
            num_cards = st.number_input("Number of cards", min_value=1, max_value=10, value=1)
            card_inputs = []
            for i in range(int(num_cards)):
                front = st.text_area(f"Front #{i + 1}", key=f"front-{selected_note['id']}-{i}")
                back = st.text_area(f"Back #{i + 1}", key=f"back-{selected_note['id']}-{i}")
                card_inputs.append((front.strip(), back.strip()))
            if st.button("Create cards", use_container_width=True):
                valid_cards = [
                    {"front": front, "back": back}
                    for front, back in card_inputs
                    if front and back
                ]
                if not valid_cards:
                    st.error("Provide at least one card front and back.")
                else:
                    rows = [
                        {
                            "deck_id": deck_id,
                            "owner": user.id,
                            "front": card["front"],
                            "back": card["back"],
                            "note_id": selected_note["id"],
                        }
                        for card in valid_cards
                    ]
                    client.table("cards").insert(rows).execute()
                    st.success(f"Created {len(rows)} cards from note.")
                    st.experimental_rerun()

    with st.expander("Danger zone", expanded=False):
        st.warning("Deleting a note cannot be undone.")
        confirm = st.checkbox("Confirm deletion", key=f"confirm-delete-{selected_note['id']}")
        if st.button("Delete note", type="primary", disabled=not confirm):
            client.table("notes").delete().eq("id", selected_note["id"]).execute()
            st.success("Note deleted.")
            st.experimental_rerun()
