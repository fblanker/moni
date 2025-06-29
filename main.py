import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
import uuid
from supabase import create_client, Client

# 1) Pagina‐configuratie
st.set_page_config(page_title="💰 Zakgeld Spel", layout="centered")

# 2) Supabase configuratie
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3) Login‐flow
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Inloggen")
    login_type = st.radio("Inloggen als:", ["Ouder", "Kind"], horizontal=True)

    if login_type == "Ouder":
        email = st.text_input("Email ouder", key="login_email")
        password = st.text_input("Wachtwoord", type="password", key="login_pw")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Inloggen als ouder"):
                try:
                    result = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if result.session:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.user_type = "ouder"
                        st.success(f"✅ Welkom, {email}!")
                        st.session_state["__rerun_id"] = str(uuid.uuid4())
                        st.stop()
                    else:
                        st.error("❌ Ongeldige inloggegevens")
                except Exception as e:
                    st.error(f"Login fout: {str(e)}")

        with col2:
            if st.button("➕ Ouderaccount aanmaken"):
                if not email or not password:
                    st.warning("Vul email en wachtwoord in om een account aan te maken.")
                else:
                    try:
                        result = supabase.auth.sign_up({"email": email, "password": password})
                        if result.user:
    st.success("🎉 Je account is aangemaakt! Bekijk je inbox om je e-mailadres te bevestigen. ✉️")
    st.info("Welkom bij *Zakgeld Spel* – de leukste manier om kinderen te leren omgaan met geld! 💰👧🧠")
                        else:
                            st.error("❌ Kon geen account aanmaken.")
                    except Exception as e:
                        st.error(f"Fout bij aanmaken account: {str(e)}")

    else:  # Kind login
        child_username = st.text_input("Gebruikersnaam kind")
        child_password = st.text_input("Wachtwoord", type="password")

        if st.button("Inloggen als kind"):
            if not child_username or not child_password:
                st.warning("Vul zowel gebruikersnaam als wachtwoord in.")
            else:
                login_email = f"{child_username}@moni.local"
                try:
                    result = supabase.auth.sign_in_with_password(
                        {"email": login_email, "password": child_password}
                    )
                    if result.session:
                        st.session_state.logged_in = True
                        st.session_state.user_email = login_email
                        st.session_state.user_type = "kind"
                        st.session_state.user_username = child_username
                        st.success(f"✅ Welkom terug, {child_username}!")
                        st.session_state["__rerun_id"] = str(uuid.uuid4())
                        st.stop()
                    else:
                        st.error("❌ Onjuiste inloggegevens")
                except Exception as e:
                    st.error(f"Fout bij inloggen: {str(e)}")

    st.stop()

user = st.session_state.user_email
st.write(f"🔓 Ingelogd als **{user}**")

# Nieuw: Beheerscherm voor ouders
if st.session_state.get("user_type") == "ouder":
    st.subheader("👨‍👩‍👧 Nieuw account aanmaken voor kind")

    child_username = st.text_input("Gebruikersnaam kind")
    child_password = st.text_input("Wachtwoord kind", type="password")
    child_name = st.text_input("Naam kind")

    if st.button("➕ Maak account aan"):
        if not child_username or not child_password or not child_name:
            st.warning("Vul naam, gebruikersnaam en wachtwoord in.")
        else:
            try:
                email_alias = f"{child_username}@moni.local"
                result = supabase.auth.sign_up(
                    {"email": email_alias, "password": child_password}
                )
                if result.user:
                    st.success(f"✅ Account aangemaakt voor {child_username}.")
                    supabase.table("kind_profielen").insert({
                        "ouder_email": user,
                        "kind_email": email_alias,
                        "gebruikersnaam": child_username,
                        "naam": child_name
                    }).execute()
                else:
                    st.error("❌ Account kon niet worden aangemaakt.")
            except Exception as e:
                st.error(f"Fout bij aanmaken account: {str(e)}")

    st.subheader("👨‍👧 Mijn kinderen")
    kinderen_response = supabase.table("kind_profielen").select("*").eq("ouder_email", user).execute()
    kinderen = kinderen_response.data or []

    if not kinderen:
        st.info("Je hebt nog geen kindaccounts toegevoegd.")
    else:
        kind_namen = {k['kind_email']: k['naam'] for k in kinderen}
        kind_options = list(kind_namen.items())
        selected_kind_email = st.selectbox("📂 Kies een kind om gegevens te bekijken:", kind_options, format_func=lambda x: x[1])
        user = selected_kind_email[0]  # overschrijf user met gekozen kindaccount
        st.info(f"Toon gegevens voor kind: {selected_kind_email[1]}")
