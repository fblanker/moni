# 📄 3_Beheer_Kinderen.py
import streamlit as st
from shared.supabase_client import get_supabase

supabase = get_supabase()

st.title("👨‍👧 Beheer Kinderen")

# 🔐 Check of iemand is ingelogd
if "user" not in st.session_state or not st.session_state.user:
    st.warning("🔐 Je bent niet ingelogd. [Log hier in 👉](./1_Login)")
    st.stop()

user_id = st.session_state.user.id
email = st.session_state.user.email
st.markdown(f"✅ Ingelogd als: **{email}**")

# ➕ Kind toevoegen
with st.expander("➕ Nieuw kind toevoegen"):
    naam = st.text_input("Naam van kind", key="nieuw_kind_naam")
    gebruikersnaam = st.text_input("Gebruikersnaam van kind", key="nieuw_kind_gebruikersnaam")

    if st.button("Kind toevoegen"):
        if not naam or not gebruikersnaam:
            st.warning("❗ Vul zowel de naam als gebruikersnaam in.")
        else:
            try:
                response = supabase.table("kind_profielen").insert({
                    "naam": naam,
                    "gebruikersnaam": gebruikersnaam,
                    "user_id": user_id
                }).execute()
                if response.data:
                    st.success("✅ Kind succesvol toegevoegd!")
                    st.rerun()
                else:
                    st.error(f"❌ Fout bij toevoegen kind: {response}")
            except Exception as e:
                st.error(f"❌ Fout bij toevoegen kind: {e}")

# 👨‍👧 Toon bestaande kinderen
try:
    response = supabase.table("kind_profielen").select("*").eq("user_id", user_id).execute()
    kinderen = response.data or []
    if kinderen:
        st.subheader("👧 Mijn kinderen")
        for kind in kinderen:
            st.markdown(f"**🧒 {kind['naam']}** – @{kind['gebruikersnaam']}")
    else:
        st.info("Je hebt nog geen kinderen toegevoegd.")
except Exception as e:
    st.error(f"❌ Fout bij ophalen van kinderen: {e}")
