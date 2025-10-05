"""User settings and data export page."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth
from lib.supabase_client import get_client
from lib.utils import dataframe_to_csv, render_sidebar

render_sidebar("Settings")
user = auth.current_user()
if not user:
    st.warning("Please sign in to continue.")
    st.stop()

client = get_client()

st.title("Settings")
st.caption("Manage your profile, export data, and sign out.")

profile_resp = (
    client.table("profiles")
    .select("id,full_name,avatar_url")
    .eq("id", user.id)
    .execute()
)
profile = profile_resp.data[0] if profile_resp.data else {"full_name": "", "avatar_url": ""}

with st.form("profile-form"):
    st.subheader("Profile")
    st.text("Authenticated as: " + (user.email or "Unknown"))
    full_name = st.text_input("Full name", value=profile.get("full_name") or "")
    avatar_url = st.text_input("Avatar URL", value=profile.get("avatar_url") or "")
    submitted = st.form_submit_button("Save profile", use_container_width=True)
    if submitted:
        client.table("profiles").upsert({
            "id": user.id,
            "full_name": full_name.strip() or None,
            "avatar_url": avatar_url.strip() or None,
        }).execute()
        st.success("Profile updated.")

st.subheader("Data export")
export_tables = {
    "Notes": "notes",
    "Decks": "decks",
    "Cards": "cards",
    "Reviews": "reviews",
}
for label, table in export_tables.items():
    response = client.table(table).select("*").eq("owner", user.id).execute()
    data = response.data or []
    df = pd.DataFrame(data)
    if df.empty:
        st.caption(f"No {label.lower()} to export yet.")
        continue
    csv_bytes = dataframe_to_csv(df)
    st.download_button(
        label=f"Download {label.lower()} CSV",
        data=csv_bytes,
        file_name=f"edunote_{table}.csv",
        mime="text/csv",
        key=f"export-{table}",
        use_container_width=True,
    )

st.subheader("Sign out")
if st.button("Sign out", type="primary", use_container_width=True):
    auth.sign_out()
    st.session_state.pop("redirected_to_dashboard", None)
    st.experimental_rerun()
