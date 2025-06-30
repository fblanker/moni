import streamlit as st
from shared.supabase_client import get_supabase

supabase = get_supabase()
st.set_page_config(page_title="👨‍👧 Kindbeheer", layout="centered")

if not st.session_state.get("logged_in") or st.session_state.get("user_type") != "ouder":
    st.warning("Alleen ouders kunnen kindaccounts beheren.")
    st.stop()

st.title("👨‍👧 Kindaccounts beheren")

child_username = st.text_input("👧 Gebruikersnaam kind")
child_password = st.text_input("🔑 Wachtwoord", type="password")
child_name = st.text_input("📛 Naam kind")

if st.button("➕ Kindaccount aanmaken"):
    if not child_username or not child_password or not child_name:
        st.warning("Vul alle velden in.")
    else:
        email_alias = f"{child_username}@moni.fakeuser.com"
        try:
            result = supabase.auth.sign_up({"email": email_alias, "password": child_password})
            if result.user:
                supabase.table("kind_profielen").insert({
                    "ouder_email": st.session_state.user_email,
                    "kind_email": email_alias,
                    "gebruikersnaam": child_username,
                    "naam": child_name
                }).execute()
                st.success(f"✅ Kindaccount '{child_name}' aangemaakt!")
        except Exception as e:
            st.error(f"Fout bij aanmaken account: {e}")

# Toon bestaande kinderen
kinderen = supabase.table("kind_profielen").select("*").eq("ouder_email", st.session_state.user_email).execute().data

if kinderen:
    st.subheader("📋 Mijn kinderen")
    for kind in kinderen:
        st.markdown(f"- 👧 **{kind['naam']}** (`{kind['gebruikersnaam']}`)")
else:
    st.info("Nog geen kinderen toegevoegd.")