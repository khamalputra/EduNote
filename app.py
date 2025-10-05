"""Entry point for EduNote authentication and routing."""
from __future__ import annotations

import streamlit as st

from lib import auth
from lib.supabase_client import get_client
from lib.utils import render_sidebar

st.set_page_config(page_title="EduNote", page_icon="🧠", layout="wide")

user = auth.current_user()
render_sidebar("Dashboard", show_nav=bool(user))

if user:
    if not st.session_state.get("redirected_to_dashboard"):
        st.session_state["redirected_to_dashboard"] = True
        st.switch_page("pages/1_Dashboard.py")
    st.stop()

st.title("Welcome to EduNote")
st.write("Create structured notes, flashcards, and master them using spaced repetition.")

tab_login, tab_register = st.tabs(["Sign In", "Register"])

with tab_login:
    st.subheader("Sign in to your workspace")
    with st.form("login-form"):
        email = st.text_input("Email", key="login-email")
        password = st.text_input("Password", type="password", key="login-password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        if submitted:
            ok, error = auth.sign_in(email.strip(), password)
            if ok:
                st.success("Signed in successfully. Redirecting…")
                st.experimental_rerun()
            else:
                st.error(error or "Unable to sign in.")

with tab_register:
    st.subheader("Create a new account")
    with st.form("register-form"):
        full_name = st.text_input("Full name", key="register-full-name")
        email = st.text_input("Email", key="register-email")
        password = st.text_input("Password", type="password", key="register-password")
        submitted = st.form_submit_button("Register", use_container_width=True)
        if submitted:
            ok, error = auth.sign_up(email.strip(), password, full_name.strip() or None)
            if ok:
                client = get_client()
                user = auth.current_user()
                if user:
                    client.table("profiles").upsert({"id": user.id, "full_name": full_name.strip() or None}).execute()
                st.success("Account created. Redirecting…")
                st.experimental_rerun()
            else:
                st.error(error or "Unable to register.")
