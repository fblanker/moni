import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Use secrets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = st.secrets["google"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)
sheet = client.open("data_zakgeld").sheet1

# Huidige gegevens ophalen
records = sheet.get_all_records()
vorige_spaarpot = records[-1]["Spaarpot"] if records else 0

# Streamlit UI
st.title("💰 Zakgeld Spel - Weekbudget")

week = st.number_input("Weeknummer", min_value=1, step=1)
zakgeld = st.number_input("Zakgeld deze week (€)", value=10)
huur = st.number_input("Huur (€)", value=2)
eten = st.number_input("Eten (€)", value=3)
plezier = st.number_input("Plezier (€)", value=1)
gespaard = st.number_input("Wil je sparen? (€)", value=2)

# Berekening
totaal_besteden = huur + eten + plezier + gespaard
over = zakgeld - totaal_besteden
spaarpot = vorige_spaarpot + gespaard

if st.button("Bevestig week"):
    rij = [week, zakgeld, huur, eten, plezier, gespaard, spaarpot, over]
    sheet.append_row(rij)
    st.success(f"Week {week} is opgeslagen!")
    st.balloons()

# Overzicht tonen
if records:
    df = pd.DataFrame(records)
    st.subheader("📊 Overzicht")
    st.line_chart(df[["Spaarpot", "Over"]])
    st.dataframe(df)
