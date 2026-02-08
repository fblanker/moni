import streamlit as st
from shared.supabase_client import get_supabase

try:
    supabase = get_supabase()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

st.title("🔐 Inloggen")

ouder_tab, kind_tab = st.tabs(["👨‍👩‍👧 Ouders", "🧒 Kinderen"])

with ouder_tab:
    email = st.text_input("E-mailadres")
    password = st.text_input("Wachtwoord", type="password")

    if st.button("Log in", key="ouder_login"):
        try:
            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if result.user:
                st.session_state.logged_in = True
                st.session_state.email = result.user.email
                st.session_state.user_email = result.user.email
                st.session_state.user_id = result.user.id
                if result.session:
                    st.session_state.access_token = result.session.access_token
                    st.session_state.refresh_token = result.session.refresh_token
                st.session_state.role = "ouder"
                st.session_state.login_success_message = f"✅ Welkom, {email}!"
                st.rerun()
        except Exception as e:
            st.error(f"Fout bij inloggen: {e}")

with kind_tab:
    gebruikersnaam = st.text_input("Gebruikersnaam")
    pincode = st.text_input("Pincode", type="password")

    if st.button("Log in", key="kind_login"):
        if not gebruikersnaam or not pincode:
            st.warning("Vul zowel gebruikersnaam als pincode in.")
        else:
            resp = (
                supabase.table("kind_profielen")
                .select("id, naam, gebruikersnaam, user_id, pincode")
                .eq("gebruikersnaam", gebruikersnaam)
                .maybe_single()
                .execute()
            )
            kind = resp.data
            if kind and str(kind.get("pincode")) == str(pincode):
                st.session_state.logged_in = True
                st.session_state.role = "kind"
                st.session_state.kind_id = kind["id"]
                st.session_state.kind_naam = kind["naam"]
                st.session_state.ouder_id = kind["user_id"]
                st.session_state.login_success_message = (
                    f"✅ Welkom, {kind['naam']}!"
                )
                st.rerun()
            else:
                st.error("Onjuiste gebruikersnaam of pincode.")

if "login_success_message" in st.session_state:
    st.success(st.session_state.login_success_message)
    del st.session_state.login_success_message
