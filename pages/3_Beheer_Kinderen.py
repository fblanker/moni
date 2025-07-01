# 📄 3_Beheer_Kinderen.py
import streamlit as st
from shared.supabase_client import get_supabase

supabase = get_supabase()

st.title("👨‍👧 Beheer Kinderen")

# 🔐 Check of iemand is ingelogd
if "email" not in st.session_state:
    st.warning("🔐 Je bent niet ingelogd. [Log hier in 👉](./1_Login)")
    st.stop()

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

# 📋 Kinderen tonen met opties om te bewerken of verwijderen
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
            with st.expander(f"👧 {kind['naam']} ({kind['gebruikersnaam']})"):
                nieuwe_naam = st.text_input("Naam", kind['naam'], key=f"naam_{kind['id']}")
                nieuwe_gebruikersnaam = st.text_input("Gebruikersnaam", kind['gebruikersnaam'], key=f"gebruikersnaam_{kind['id']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Wijzigingen opslaan", key=f"opslaan_{kind['id']}"):
                        try:
                            update_response = supabase.table("kind_profielen") \
                                .update({
                                    "naam": nieuwe_naam,
                                    "gebruikersnaam": nieuwe_gebruikersnaam
                                }) \
                                .eq("id", kind["id"]) \
                                .execute()

                            if update_response.data:
                                st.success("✅ Gegevens bijgewerkt!")
                                st.rerun()
                            else:
                                st.error("❌ Fout bij bijwerken kind.")
                        except Exception as e:
                            st.error(f"❌ Fout bij bijwerken kind: {e}")

                with col2:
                    if st.button("🗑️ Verwijderen", key=f"verwijderen_{kind['id']}"):
                        try:
                            delete_response = supabase.table("kind_profielen") \
                                .delete() \
                                .eq("id", kind["id"]) \
                                .execute()

                            if delete_response.data:
                                st.success("🗑️ Kind verwijderd.")
                                st.rerun()
                            else:
                                st.error("❌ Fout bij verwijderen kind.")
                        except Exception as e:
                            st.error(f"❌ Fout bij verwijderen kind: {e}")
except Exception as e:
    st.error(f"❌ Fout bij ophalen kinderen: {e}")
