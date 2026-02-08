# 📄 pages/3_Beheer_Kinderen.py
import streamlit as st
from shared.supabase_client import get_supabase

try:
    supabase = get_supabase()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

# ————————————————
# 1) Check Streamlit session_state, not supabase.auth.get_user()
if not st.session_state.get("logged_in"):
    st.warning("🔐 Je bent niet ingelogd. [Log hier in 👉](./1_Login)")
    st.stop()

if st.session_state.get("role") != "ouder":
    st.warning("Deze pagina is alleen voor ouders.")
    st.stop()

ouder_email = st.session_state.get("email") or st.session_state.get("user_email")
ouder_id    = st.session_state.user_id  # set this when you log in!

# ————————————————
# 2) Show who’s logged in
st.markdown(f"✅ Ingelogd als: **{ouder_email}**")

# ————————————————
# 3) “Add Child” form
with st.expander("➕ Nieuw kind toevoegen"):
    naam = st.text_input("Naam van kind", key="nieuw_kind_naam")
    usern = st.text_input("Gebruikersnaam", key="nieuw_kind_usern")
    pincode = st.text_input("Pincode (4 cijfers)", type="password", key="nieuw_kind_pincode")

    st.markdown("**Spelinstellingen**")
    allowance = st.number_input("Wekelijkse allowance/loon (€)", min_value=0.0, value=5.0, step=0.5)
    huur = st.number_input("Huur (€)", min_value=0.0, value=3.0, step=0.5)
    eten = st.number_input("Eten (€)", min_value=0.0, value=1.0, step=0.5)
    sparen_rente = st.number_input("Sparen rente (% per week)", min_value=0.0, value=1.0, step=0.5)
    investeren_rente = st.number_input("Investeren rendement (% per week)", min_value=0.0, value=3.0, step=0.5)

    if st.button("Kind toevoegen", key="knop_toevoegen_kind"):
        if not naam or not usern or not pincode:
            st.warning("Vul naam, gebruikersnaam en pincode in.")
        else:
            resp = supabase.table("kind_profielen").insert({
                "naam": naam,
                "gebruikersnaam": usern,
                "pincode": pincode,
                "user_id": ouder_id,
                "allowance": allowance,
                "huur": huur,
                "eten": eten,
                "sparen_rente": sparen_rente,
                "investeren_rente": investeren_rente
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
        st.markdown(
            f"👧 **{kind['naam']}** (@{kind['gebruikersnaam']}) — "
            f"Allowance: €{kind.get('allowance', 0)} | "
            f"Huur: €{kind.get('huur', 0)} | Eten: €{kind.get('eten', 0)}"
        )
        with st.expander(f"⚙️ Instellingen voor {kind['naam']}"):
            allowance = st.number_input(
                "Wekelijkse allowance/loon (€)",
                min_value=0.0,
                value=float(kind.get("allowance", 5)),
                step=0.5,
                key=f"allowance_{kind['id']}"
            )
            huur = st.number_input(
                "Huur (€)",
                min_value=0.0,
                value=float(kind.get("huur", 3)),
                step=0.5,
                key=f"huur_{kind['id']}"
            )
            eten = st.number_input(
                "Eten (€)",
                min_value=0.0,
                value=float(kind.get("eten", 1)),
                step=0.5,
                key=f"eten_{kind['id']}"
            )
            sparen_rente = st.number_input(
                "Sparen rente (% per week)",
                min_value=0.0,
                value=float(kind.get("sparen_rente", 1)),
                step=0.5,
                key=f"sparen_{kind['id']}"
            )
            investeren_rente = st.number_input(
                "Investeren rendement (% per week)",
                min_value=0.0,
                value=float(kind.get("investeren_rente", 3)),
                step=0.5,
                key=f"investeren_{kind['id']}"
            )
            pincode = st.text_input(
                "Pincode (laat leeg om niet te wijzigen)",
                type="password",
                key=f"pincode_{kind['id']}"
            )
            if st.button("Instellingen opslaan", key=f"opslaan_{kind['id']}"):
                update_data = {
                    "allowance": allowance,
                    "huur": huur,
                    "eten": eten,
                    "sparen_rente": sparen_rente,
                    "investeren_rente": investeren_rente
                }
                if pincode:
                    update_data["pincode"] = pincode
                resp = (
                    supabase.table("kind_profielen")
                    .update(update_data)
                    .eq("id", kind["id"])
                    .execute()
                )
                if resp.data:
                    st.success("✅ Instellingen bijgewerkt!")
                    st.rerun()
                else:
                    st.error("❌ Kon instellingen niet opslaan.")
