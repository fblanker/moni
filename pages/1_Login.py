import streamlit as st
from shared.supabase_client import get_supabase

supabase = get_supabase()

st.title("🔐 Inloggen")

email = st.text_input("E-mailadres")
password = st.text_input("Wachtwoord", type="password")

if st.button("Log in"):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if result.user:
            st.session_state.logged_in = True
            st.session_state.email = email
            st.session_state.login_success_message = f"✅ Welkom, {email}!"
            st.rerun()
    except Exception as e:
        st.error(f"Fout bij inloggen: {e}")

if "login_success_message" in st.session_state:
    st.success(st.session_state.login_success_message)
    del st.session_state.login_success_message