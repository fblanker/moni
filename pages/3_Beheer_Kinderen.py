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

# 🧒 Kindgegevens ophalen
try:
    response = supabase.table("kind_profielen")\
        .select("*")\
        .eq("email", st.session_state.email)\
        .execute()
    kinderen = response.data or []

    if not kinderen:
        st.info("Er zijn nog geen kinderen gekoppeld aan dit account.")
    else:
        for kind in kinderen:
            with st.expander(f"👧 {kind['naam']}"):
                st.text_input("Naam", value=kind['naam'], key=f"naam_{kind['id']}")
                st.text_input("Gebruikersnaam", value=kind['gebruikersnaam'], key=f"user_{kind['id']}")

                if st.button("💾 Opslaan", key=f"save_{kind['id']}"):
                    updated = supabase.table("kind_profielen").update({
                        "naam": st.session_state[f"naam_{kind['id']}"],
                        "gebruikersnaam": st.session_state[f"user_{kind['id']}"],
                    }).eq("id", kind["id"]).execute()

                    if updated.status_code == 200:
                        st.success("✅ Gegevens opgeslagen")
                    else:
                        st.error(f"❌ Fout bij opslaan: {updated.data}")
except Exception as e:
    st.error(f"Fout bij ophalen kindgegevens: {e}")
