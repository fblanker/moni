import streamlit as st
from shared.supabase_client import get_supabase

supabase = get_supabase()
st.set_page_config(page_title="👨‍👧 Kindbeheer", layout="centered")

if not st.session_state.get("logged_in") or st.session_state.get("user_type") != "ouder":
    st.warning("Alleen ouders kunnen kindaccounts beheren.")
    st.stop()

st.title("👨‍👧 Kindaccounts beheren")

# Authenticated Supabase-gebruiker ophalen
auth_user = supabase.auth.get_user()
if not auth_user or not auth_user.user or not auth_user.user.email:
    st.error("Fout: geen actieve Supabase-sessie gevonden. Log opnieuw in.")
    st.stop()

ouder_email = auth_user.user.email  # Gebruik email van Supabase sessie (werkt met RLS!)

# Nieuw kindaccount aanmaken
st.subheader("➕ Nieuw kindaccount")
child_username = st.text_input("👧 Gebruikersnaam kind")
child_password = st.text_input("🔑 Wachtwoord", type="password")
child_name = st.text_input("📛 Naam kind")

if st.button("✅ Kindaccount aanmaken"):
    if not child_username or not child_password or not child_name:
        st.warning("Vul alle velden in.")
    else:
        email_alias = f"{child_username}@moni.fakeuser.com"
        try:
            result = supabase.auth.sign_up({"email": email_alias, "password": child_password})
            if result.user:
                supabase.table("kind_profielen").insert({
                    "ouder_email": ouder_email,
                    "kind_email": email_alias,
                    "gebruikersnaam": child_username,
                    "naam": child_name
                }).execute()
                st.success(f"✅ Kindaccount '{child_name}' aangemaakt!")
                st.rerun()
        except Exception as e:
            st.error(f"Fout bij aanmaken account: {e}")

# Bestaande kinderen tonen en bewerken
st.subheader("📋 Mijn kinderen")
kinderen = supabase.table("kind_profielen").select("*").eq("ouder_email", ouder_email).execute().data

if not kinderen:
    st.info("Nog geen kinderen toegevoegd.")
else:
    for kind in kinderen:
        with st.expander(f"👧 {kind['naam']} ({kind['gebruikersnaam']})", expanded=False):
            new_naam = st.text_input(f"Naam voor {kind['gebruikersnaam']}", value=kind['naam'], key=f"naam_{kind['id']}")
            new_gebruikersnaam = st.text_input(f"Gebruikersnaam", value=kind['gebruikersnaam'], key=f"user_{kind['id']}")
            if st.button("💾 Opslaan", key=f"save_{kind['id']}"):
                try:
                    supabase.table("kind_profielen").update({
                        "naam": new_naam,
                        "gebruikersnaam": new_gebruikersnaam
                    }).eq("id", kind['id']).execute()
                    st.success("Kindgegevens bijgewerkt ✅")    
                    st.rerun()
                except Exception as e:
                    st.error(f"Fout bij opslaan: {e}")
            if st.button("🗑️ Verwijder kindaccount", key=f"delete_{kind['id']}"):
                try:
                    supabase.table("kind_profielen").delete().eq("id", kind['id']).execute()
                    st.success("Kindaccount verwijderd ❌")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fout bij verwijderen: {e}")