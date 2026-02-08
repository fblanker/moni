import streamlit as st
from shared.supabase_client import get_supabase
from datetime import date

try:
    supabase = get_supabase()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()
st.set_page_config(page_title="💰 Moni Spel", layout="centered")

if not st.session_state.get("logged_in"):
    st.warning("Log eerst in om dit spel te spelen.")
    st.stop()

role = st.session_state.get("role", "ouder")
today = date.today()
weeknum, year = today.isocalendar().week, today.year
week_id = f"Week {weeknum} - {year}"

st.title("💰 Moni: Zakgeld Spel")
st.markdown(f"**Week:** {week_id}")

def get_kind_profiel(kind_id):
    resp = (
        supabase.table("kind_profielen")
        .select("*")
        .eq("id", kind_id)
        .maybe_single()
        .execute()
    )
    return resp.data

def get_kinderen(ouder_id):
    resp = (
        supabase.table("kind_profielen")
        .select("id, naam, gebruikersnaam")
        .eq("user_id", ouder_id)
        .execute()
    )
    return resp.data or []

kind_id = st.session_state.get("kind_id")
if role == "ouder":
    kinderen = get_kinderen(st.session_state.get("user_id"))
    if not kinderen:
        st.info("Voeg eerst een kind toe bij 'Beheer Kinderen'.")
        st.stop()
    opties = {f"{k['naam']} (@{k['gebruikersnaam']})": k["id"] for k in kinderen}
    keuze = st.selectbox("Voor welk kind speel je deze week?", list(opties.keys()))
    kind_id = opties[keuze]
    st.session_state.kind_id = kind_id
elif not kind_id:
    st.warning("Selecteer eerst een kind of log in als ouder.")
    st.stop()

kind_profiel = get_kind_profiel(kind_id)
if not kind_profiel:
    st.error("Kon het kind-profiel niet laden.")
    st.stop()

allowance = float(kind_profiel.get("allowance", 5))
huur = float(kind_profiel.get("huur", 3))
eten = float(kind_profiel.get("eten", 1))
sparen_rente = float(kind_profiel.get("sparen_rente", 1))
investeren_rente = float(kind_profiel.get("investeren_rente", 3))
totale_kosten = huur + eten

klusjes = st.number_input("💪 Verdiend met klusjes (€)", min_value=0, value=0)
opname = st.number_input("🏧 Geld opnemen (€)", min_value=0, value=0)

response = (
    supabase.table("zakgeld_data")
    .select("*")
    .eq("kind_id", kind_id)
    .execute()
)
data = response.data or []
prev_balance = float(data[-1]["Totaal_Over"]) if data else 0

inkomen = allowance + klusjes
uitgaven = totale_kosten
nieuw_saldo = prev_balance + inkomen - uitgaven - opname

st.subheader("💡 Wat doe je met het geld dat over is?")
keuze = st.radio(
    "Kies een optie",
    (
        f"💚 Sparen ({sparen_rente:.1f}% rente)",
        f"🚀 Investeren ({investeren_rente:.1f}% rendement)"
    ),
)

if "Sparen" in keuze:
    rente = sparen_rente / 100
    actie = "sparen"
else:
    rente = investeren_rente / 100
    actie = "investeren"

nieuw_saldo_met_rente = nieuw_saldo * (1 + rente)

st.markdown(
    f"**Allowance:** €{allowance:.2f} | **Huur:** €{huur:.2f} | **Eten:** €{eten:.2f}"
)
st.markdown(f"**Saldo na kosten:** €{nieuw_saldo:.2f}")
st.markdown(f"**Saldo na {actie}:** €{nieuw_saldo_met_rente:.2f}")

if st.button("✅ Bevestig week"):
    row = {
        "kind_id": kind_id,
        "ouder_id": kind_profiel.get("user_id"),
        "Week_ID": week_id,
        "Inkomen": inkomen,
        "Uitgaven": uitgaven,
        "Opgenomen": opname,
        "Actie": actie,
        "Rente": rente,
        "Totaal_Over": nieuw_saldo_met_rente
    }
    supabase.table("zakgeld_data").insert(row).execute()
    st.success("Week opgeslagen!")
    st.rerun()
