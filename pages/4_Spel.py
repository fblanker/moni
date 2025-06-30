import streamlit as st
from shared.supabase_client import get_supabase
from datetime import date

supabase = get_supabase()
st.set_page_config(page_title="💰 Moni Spel", layout="centered")

if not st.session_state.get("logged_in"):
    st.warning("Log eerst in om dit spel te spelen.")
    st.stop()

user = st.session_state.get("user_email")
today = date.today()
weeknum, year = today.isocalendar().week, today.year
week_id = f"Week {weeknum} - {year}"

st.title("💰 Moni: Zakgeld Spel")
st.markdown(f"**Week:** {week_id}")

ZAKGELD = 5
HUUR = 3
ETEN = 1
TOTAAL_KOSTEN = HUUR + ETEN

klusjes = st.number_input("💪 Verdiend met klusjes (€)", min_value=0, value=0)
opname = st.number_input("🏧 Geld opnemen (€)", min_value=0, value=0)

response = supabase.table("zakgeld_data").select("*").eq("email", user).execute()
data = response.data or []
prev_balance = float(data[-1]["Totaal_Over"]) if data else 0

inkomen = ZAKGELD + klusjes
uitgaven = TOTAAL_KOSTEN
nieuw_saldo = prev_balance + inkomen - uitgaven - opname

if st.button("✅ Bevestig week"):
    row = {
        "email": user,
        "Week_ID": week_id,
        "Inkomen": inkomen,
        "Uitgaven": uitgaven,
        "Opgenomen": opname,
        "Totaal_Over": nieuw_saldo
    }
    supabase.table("zakgeld_data").insert(row).execute()
    st.success("Week opgeslagen!")
    st.rerun()