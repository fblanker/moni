import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date

# Google Sheets authenticatie via Streamlit secrets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("zakgeld_data").sheet1

# Ophalen vorige records
records = sheet.get_all_records()
vorige_cumulatief = records[-1]["Totaal Over"] if records else 0

# Instellingen
ZAKGELD_PER_WEEK = 5
VASTE_KOSTEN_HUUR = 3
VASTE_KOSTEN_ETEN = 1

st.title("💰 Zakgeld Spel")

# Automatisch week en jaar bepalen
vandaag = date.today()
weeknummer = vandaag.isocalendar().week
jaar = vandaag.year
week_id = f"Week {weeknummer} - {jaar}"

st.markdown(f"**Huidige week:** {week_id}")
st.markdown(f"**Zakgeld:** €{ZAKGELD_PER_WEEK}")
st.markdown(f"**Vaste lasten:** Huur €{VASTE_KOSTEN_HUUR} + Eten €{VASTE_KOSTEN_ETEN}")

st.subheader("📋 Invoer voor deze week")

klusjes_verdiensten = st.number_input("Geld verdiend met klusjes (€)", min_value=0, value=0)
gespaard = st.number_input("Geld om te sparen (€)", min_value=0, value=0)
uitgegeven = st.number_input("Geld uitgegeven (€)", min_value=0, value=0)

# Berekeningen
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

# Visualisatie overzicht
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
