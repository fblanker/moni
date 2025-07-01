# 📄 pages/3_Beheer_Kinderen.py
import streamlit as st
from shared.supabase_client import get_supabase

supabase = get_supabase()

# ————————————————
# 1) Check Streamlit session_state, not supabase.auth.get_user()
if not st.session_state.get("logged_in"):
    st.warning("🔐 Je bent niet ingelogd. [Log hier in 👉](./1_Login)")
    st.stop()

ouder_email = st.session_state.email
ouder_id    = st.session_state.user_id  # set this when you log in!

# ————————————————
# 2) Show who’s logged in
st.markdown(f"✅ Ingelogd als: **{ouder_email}**")

# ————————————————
# 3) “Add Child” form
with st.expander("➕ Nieuw kind toevoegen"):
    naam  = st.text_input("Naam van kind", key="nieuw_kind_naam")
    usern = st.text_input("Gebruikersnaam", key="nieuw_kind_usern")

    if st.button("Kind toevoegen", key="knop_toevoegen_kind"):
        if not naam or not usern:
            st.warning("Vul zowel naam als gebruikersnaam in.")
        else:
            resp = supabase.table("kind_profielen").insert({
                "naam": naam,
                "gebruikersnaam": usern,
                "user_id": ouder_id
            }).execute()
            if resp.data:
                st.success("✅ Kind toegevoegd!")
                st.rerun()
            else:
                st.error(f"❌ Fout: {resp}")

# ————————————————
# 4) Fetch & display children
st.subheader("📋 Jouw kinderen")
resp = supabase.table("kind_profielen") \
    .select("*") \
    .eq("user_id", ouder_id) \
    .execute()

kinderen = resp.data or []
if not kinderen:
    st.info("Je hebt nog geen kinderen toegevoegd.")
else:
    for kind in kinderen:
        st.markdown(f"👧 **{kind['naam']}** (@{kind['gebruikersnaam']})")
