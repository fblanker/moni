import streamlit as st
import pandas as pd
import altair as alt
from shared.supabase_client import get_supabase

supabase = get_supabase()
st.set_page_config(page_title="📊 Overzicht", layout="centered")

if not st.session_state.get("logged_in"):
    st.warning("Log eerst in om je overzicht te bekijken.")
    st.stop()

user = st.session_state.get("user_email")
response = supabase.table("zakgeld_data").select("*").eq("email", user).execute()
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