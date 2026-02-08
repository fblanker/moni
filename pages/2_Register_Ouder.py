import streamlit as st
from shared.supabase_client import get_app_base_url, get_supabase

try:
    supabase = get_supabase()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

st.set_page_config(page_title="📝 Registreer als Ouder", layout="centered")
st.title("📝 Registreer je als ouder")
st.info("Maak hier een ouder-account aan. Daarna kun je kinderen toevoegen en hun spel instellen.")

email = st.text_input("✉️ E-mailadres")
password = st.text_input("🔑 Kies een wachtwoord", type="password")

if st.button("➕ Account aanmaken"):
    if not email or not password:
        st.warning("Vul zowel e-mailadres als wachtwoord in.")
    else:
        try:
            app_base_url = get_app_base_url()
            payload = {"email": email, "password": password}
            if app_base_url:
                payload["options"] = {"email_redirect_to": app_base_url}
            result = supabase.auth.sign_up(payload)
            if result.user:
                st.success("🎉 Je account is aangemaakt! Bekijk je inbox om je e-mailadres te bevestigen. ✉️")
                st.info("Welkom bij *Moni* – de leukste manier om kinderen te leren omgaan met geld! 💰👧🧠")
            else:
                st.error("❌ Kon geen account aanmaken.")
        except Exception as e:
            st.error(f"Fout bij aanmaken account: {e}")
