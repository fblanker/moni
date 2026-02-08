import streamlit as st
import pandas as pd
import altair as alt
from shared.supabase_client import get_supabase

try:
    supabase = get_supabase()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()
st.set_page_config(page_title="📊 Overzicht", layout="centered")

if not st.session_state.get("logged_in"):
    st.warning("Log eerst in om je overzicht te bekijken.")
    st.stop()

role = st.session_state.get("role", "ouder")
kind_id = st.session_state.get("kind_id")

if role == "ouder":
    kinderen = (
        supabase.table("kind_profielen")
        .select("id, naam, gebruikersnaam")
        .eq("user_id", st.session_state.get("user_id"))
        .execute()
        .data
        or []
    )
    if not kinderen:
        st.info("Voeg eerst een kind toe bij 'Beheer Kinderen'.")
        st.stop()
    opties = {f"{k['naam']} (@{k['gebruikersnaam']})": k["id"] for k in kinderen}
    keuze = st.selectbox("Kies een kind", list(opties.keys()))
    kind_id = opties[keuze]
    st.session_state.kind_id = kind_id
elif not kind_id:
    st.warning("Selecteer eerst een kind of log in als ouder.")
    st.stop()

if not kind_id:
    st.warning("Selecteer eerst een kind.")
    st.stop()

response = (
    supabase.table("zakgeld_data")
    .select("*")
    .eq("kind_id", kind_id)
    .execute()
)
records = response.data or []

st.title("📊 Financieel Overzicht")

if not records:
    st.info("Nog geen gegevens beschikbaar.")
    st.stop()

df = pd.DataFrame(records)
df["Week_ID"] = pd.Categorical(df["Week_ID"], ordered=True)
df = df.sort_values("Week_ID")

st.dataframe(df)

chart = alt.Chart(df).mark_line().encode(
    x="Week_ID:N",
    y="Totaal_Over:Q"
).properties(title="📈 Cumulatief Saldo", width=700)

st.altair_chart(chart, use_container_width=True)
