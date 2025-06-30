# 📄 3_Beheer_Kinderen.py
import streamlit as st
from shared.supabase_client import get_supabase

supabase = get_supabase()

st.title("👨‍👧 Beheer Kinderen")

# 🔐 Check of iemand is ingelogd
if "email" not in st.session_state:
    st.warning("🔐 Je bent niet ingelogd. [Log hier in 👉](./1_Login)")
    st.stop()

# ✅ Toon ingelogd e-mailadres
st.markdown(f"✅ Ingelogd als: **{st.session_state.email}**")

# ➕ Kind toevoegen
with st.expander("➕ Nieuw kind toevoegen"):
    nieuwe_naam = st.text_input("Naam van kind", key="nieuw_naam")
    nieuwe_gebruikersnaam = st.text_input("Gebruikersnaam van kind", key="nieuw_gebruikersnaam")

    if st.button("Kind toevoegen"):
        if not nieuwe_naam or not nieuwe_gebruikersnaam:
            st.warning("Vul zowel de naam als gebruikersnaam in.")
        else:
            try:
                response = supabase.table("kind_profielen").insert({
                    "email": st.session_state.email,
                    "naam": nieuwe_naam,
                    "gebruikersnaam": nieuwe_gebruikersnaam
                }).execute()

                if response.status_code == 201:
                    st.success("✅ Kind toegevoegd!")
                    st.rerun()
                else:
                    st.error(f"❌ Fout bij toevoegen kind: {response.data}")
            except Exception as e:
                st.error(f"❌ Fout bij toevoegen kind: {e}")
