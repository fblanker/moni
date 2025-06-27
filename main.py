import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime

# 🔐 Google Sheets authenticatie via Streamlit secrets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = dict(st.secrets["google"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("zakgeld_data").sheet1

# 📥 Vorige records ophalen
records = sheet.get_all_records()
vorige_cumulatief = records[-1]["Totaal Over"] if records else 0

# 📌 Instellingen
ZAKGELD_PER_WEEK = 5
VASTE_KOSTEN_HUUR = 3
VASTE_KOSTEN_ETEN = 1

st.title("💰 Zakgeld Spel")

# 📆 Week + jaar invoer
jaar = st.number_input("Jaar", min_value=2023, max_value=2100, value=datetime.now().year)
week = st.number_input("Weeknummer", min_value=1, max_value=53, value=datetime.now().isocalendar().week)
week_id = f"Week {int(week)} - {int(jaar)}"

st.subheader("📋 Invoer van deze week")

klusjes_verdiensten = st.number_input("Geld verdiend met klusjes (€)", min_value=0, value=0)
gespaard = st.number_input("Geld om te sparen (€)", min_value=0, value=0)
uitgegeven = st.number_input("Geld uitgegeven (€)", min_value=0, value=0)

# 💶 Berekeningen
inkomen = ZAKGELD_PER_WEEK + klusjes_verdiensten
uitgaven = VASTE_KOSTEN_HUUR + VASTE_KOSTEN_ETEN + gespaard + uitgegeven
over = inkomen - uitgaven
cumulatief = vorige_cumulatief + over

if over < 0:
    st.warning("⚠️ Je hebt meer uitgegeven dan je inkomen!")

if st.button("✅ Bevestig deze week"):
    rij = [
        week_id, inkomen, VASTE_KOSTEN_HUUR, VASTE_KOSTEN_ETEN,
        klusjes_verdiensten, gespaard, uitgegeven, over, cumulatief
    ]
    sheet.append_row(rij)
    st.success(f"Week {week_id} opgeslagen!")
    st.balloons()

# 📊 Overzicht en visualisatie
st.subheader("📈 Overzicht")

df = pd.DataFrame(sheet.get_all_records())
if not df.empty:
    df.rename(columns={"Week ID": "Week"}, inplace=True)

    col1, col2 = st.columns(2)

    with col1:
        st.write("📊 Inkomsten vs Uitgaven")
        st.line_chart(df[["Inkomen", "Huur", "Eten", "Klusjes", "Uitgegeven"]])

    with col2:
        st.write("📈 Cumulatief overgebleven bedrag")
        st.line_chart(df["Totaal Over"])

    st.write("📄 Volledige gegevens")
    st.dataframe(df)
