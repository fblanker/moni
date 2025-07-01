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
ouder_email = st.session_state.email
st.markdown(f"✅ Ingelogd als: **{ouder_email}**")

# ➕ Kind toevoegen
with st.expander("➕ Nieuw kind toevoegen"):
    nieuwe_naam = st.text_input("Naam van kind", key="nieuw_naam_kind")
    nieuwe_gebruikersnaam = st.text_input("Gebruikersnaam van kind", key="nieuw_gebruikersnaam_kind")

    if st.button("Kind toevoegen"):
        if not nieuwe_naam or not nieuwe_gebruikersnaam:
            st.warning("Vul zowel de naam als gebruikersnaam in.")
        else:
            try:
                response = supabase.table("kind_profielen").insert({
                    "email": ouder_email,
                    "naam": nieuwe_naam,
                    "gebruikersnaam": nieuwe_gebruikersnaam
                }).execute()

                if response.data:
                    st.success("✅ Kind toegevoegd!")
                    st.rerun()
                else:
                    st.error(f"❌ Fout bij toevoegen kind: {response}")
            except Exception as e:
                st.error(f"❌ Fout bij toevoegen kind: {e}")

# 👧 Kinderen van deze ouder ophalen en tonen
try:
    kinderen_response = supabase.table("kind_profielen") \
        .select("*") \
        .eq("email", ouder_email) \
        .execute()

    kinderen = kinderen_response.data or []

    if not kinderen:
        st.info("Je hebt nog geen kinderen toegevoegd.")
    else:
        st.subheader("📋 Mijn kinderen")
        for kind in kinderen:
            st.markdown(f"👧 **{kind['naam']}** – _Gebruikersnaam:_ `{kind['gebruikersnaam']}`")
except Exception as e:
    st.error(f"❌ Fout bij ophalen kinderen: {e}")
