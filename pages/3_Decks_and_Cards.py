"""Deck and card management page."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth
from lib.supabase_client import get_client
from lib.utils import dataframe_to_csv, read_uploaded_csv, render_sidebar

render_sidebar("Decks & Cards")
user = auth.current_user()
if not user:
    st.warning("Please sign in to continue.")
    st.stop()

client = get_client()

st.title("Decks & Cards")
st.caption("Organize decks and manage flashcards.")

with st.form("new-deck"):
    st.subheader("Create deck")
    deck_name = st.text_input("Deck name")
    deck_desc = st.text_area("Description", height=100)
    create_deck = st.form_submit_button("Create deck", use_container_width=True)
    if create_deck:
        if not deck_name.strip():
            st.error("Deck name is required.")
        else:
            client.table("decks").insert({
                "name": deck_name.strip(),
                "description": deck_desc,
                "owner": user.id,
            }).execute()
            st.success("Deck created.")
            st.experimental_rerun()

decks_resp = (
    client.table("decks")
    .select("id,name,description,created_at,updated_at")
    .eq("owner", user.id)
    .order("name")
    .execute()
)
decks = decks_resp.data or []

if not decks:
    st.info("Create a deck to begin managing cards.")
    st.stop()

deck_lookup = {deck["name"]: deck for deck in decks}
selected_name = st.selectbox("Select deck", options=list(deck_lookup.keys()))
selected_deck = deck_lookup[selected_name]

with st.form("edit-deck"):
    new_name = st.text_input("Deck name", value=selected_deck["name"])
    new_desc = st.text_area("Description", value=selected_deck.get("description") or "")
    update_deck = st.form_submit_button("Save changes", use_container_width=True)
    if update_deck:
        client.table("decks").update({
            "name": new_name.strip(),
            "description": new_desc,
        }).eq("id", selected_deck["id"]).execute()
        st.success("Deck updated.")
        st.experimental_rerun()

with st.expander("Danger zone"):
    st.warning("Deleting a deck removes all cards in it.")
    confirm_delete = st.checkbox("Confirm deck deletion", key=f"delete-{selected_deck['id']}")
    if st.button("Delete deck", type="primary", disabled=not confirm_delete):
        client.table("decks").delete().eq("id", selected_deck["id"]).execute()
        st.success("Deck deleted.")
        st.experimental_rerun()

cards_resp = (
    client.table("cards")
    .select("id,front,back,suspended,due_at,interval_days,ease,note_id")
    .eq("owner", user.id)
    .eq("deck_id", selected_deck["id"])
    .order("created_at")
    .execute()
)
cards = cards_resp.data or []

st.subheader("Cards")
if cards:
    cards_df = pd.DataFrame(cards)
    display_df = cards_df.set_index("id")[["front", "back", "suspended"]]
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        key=f"cards-editor-{selected_deck['id']}",
    )
    if st.button("Save card changes", use_container_width=True):
        updates = []
        for card_id, row in edited_df.iterrows():
            original = display_df.loc[card_id]
            if not original.equals(row):
                updates.append(
                    {
                        "id": card_id,
                        "front": row["front"],
                        "back": row["back"],
                        "suspended": bool(row["suspended"]),
                    }
                )
        if updates:
            for payload in updates:
                cid = payload.pop("id")
                client.table("cards").update(payload).eq("id", cid).execute()
            st.success(f"Updated {len(updates)} cards.")
        else:
            st.info("No changes to save.")
        st.experimental_rerun()
else:
    st.info("No cards in this deck yet.")

st.subheader("CSV tools")
export_col, import_col = st.columns(2)
with export_col:
    if cards:
        export_bytes = dataframe_to_csv(pd.DataFrame(cards))
        st.download_button(
            label="Download cards CSV",
            data=export_bytes,
            file_name=f"{selected_deck['name'].replace(' ', '_').lower()}_cards.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.caption("Add cards to enable export.")

with import_col:
    uploaded = st.file_uploader("Upload cards CSV", type=["csv"], key=f"cards-upload-{selected_deck['id']}")
    if uploaded and st.button("Import cards", use_container_width=True):
        df = read_uploaded_csv(uploaded)
        required_columns = {"front", "back"}
        if not required_columns.issubset(df.columns):
            st.error("CSV must include 'front' and 'back' columns.")
        else:
            rows = []
            for _, row in df.iterrows():
                deck_name = row.get("deck") if "deck" in df.columns else None
                if pd.isna(deck_name) or not deck_name:
                    deck_id = selected_deck["id"]
                else:
                    deck = deck_lookup.get(str(deck_name))
                    if not deck:
                        st.error(f"Deck '{deck_name}' does not exist.")
                        st.stop()
                    deck_id = deck["id"]
                front = str(row.get("front", "")).strip()
                back = str(row.get("back", "")).strip()
                if front and back:
                    rows.append(
                        {
                            "deck_id": deck_id,
                            "owner": user.id,
                            "front": front,
                            "back": back,
                        }
                    )
            if not rows:
                st.error("No valid cards found in CSV.")
            else:
                client.table("cards").insert(rows).execute()
                st.success(f"Imported {len(rows)} cards.")
                st.experimental_rerun()
