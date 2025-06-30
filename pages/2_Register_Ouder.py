import streamlit as st
from shared.supabase_client import get_supabase

supabase = get_supabase()

st.set_page_config(page_title="📝 Registreer als Ouder", layout="centered")
st.title("📝 Registreer je als ouder")

email = st.text_input("✉️ E-mailadres")
password = st.text_input("🔑 Kies een wachtwoord", type="password")

if st.button("➕ Account aanmaken"):
    if not email or not password:
        st.warning("Vul zowel e-mailadres als wachtwoord in.")
    else:
        try:
            result = supabase.auth.sign_up({"email": email, "password": password})
            if result.user:
                st.success("🎉 Je account is aangemaakt! Bekijk je inbox om je e-mailadres te bevestigen. ✉️")
                st.info("Welkom bij *Moni* – de leukste manier om kinderen te leren omgaan met geld! 💰👧🧠")
            else:
                st.error("❌ Kon geen account aanmaken.")
        except Exception as e:
            st.error(f"Fout bij aanmaken account: {e}")