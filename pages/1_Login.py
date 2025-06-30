# 📄 moni/pages/1_Login.py
import streamlit as st
from shared.supabase_client import get_supabase
import uuid

supabase = get_supabase()

st.set_page_config(page_title="🔐 Inloggen", layout="centered")
st.title("🔐 Inloggen bij Moni")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

login_type = st.radio("Inloggen als:", ["Ouder", "Kind"], horizontal=True)

if login_type == "Ouder":
    email = st.text_input("✉️ E-mailadres ouder")
    password = st.text_input("🔑 Wachtwoord", type="password")

    if st.button("Inloggen als ouder"):
        try:
            result = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if result.session:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_type = "ouder"
                st.success(f"✅ Welkom terug, {email}!")
                st.rerun()
            else:
                st.error("❌ Ongeldige inloggegevens")
        except Exception as e:
            st.error(f"Fout bij inloggen: {e}")

else:  # Kind-login
    gebruikersnaam = st.text_input("👧 Gebruikersnaam kind")
    wachtwoord = st.text_input("🔑 Wachtwoord", type="password")

    if st.button("Inloggen als kind"):
        if not gebruikersnaam or not wachtwoord:
            st.warning("Vul zowel gebruikersnaam als wachtwoord in.")
        else:
            login_email = f"{gebruikersnaam}@moni.fakeuser.com"
            try:
                result = supabase.auth.sign_in_with_password(
                    {"email": login_email, "password": wachtwoord}
                )
                if result.session:
                    st.session_state.logged_in = True
                    st.session_state.user_email = login_email
                    st.session_state.user_type = "kind"
                    st.session_state.user_username = gebruikersnaam
                    st.success(f"✅ Welkom terug, {gebruikersnaam}!")
                    st.rerun()
                else:
                    st.error("❌ Onjuiste gebruikersnaam of wachtwoord")
            except Exception as e:
                st.error(f"Fout bij inloggen: {e}")
