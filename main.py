import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import altair as alt

# --- Simpele login ---
USERS = {
    "nayeli": "30082019",
    "royel": "10122019",
    "cayen": "24042020"
}

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 Inloggen")
        username = st.text_input("Gebruikersnaam")
        password = st.text_input("Wachtwoord", type="password")
        if st.button("Inloggen"):
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.experimental_rerun()
            else:
                st.error("Foutieve gebruikersnaam of wachtwoord")
        st.stop()

# Roep login aan
login()

# Stop als niet ingelogd
if not st.session_state.get("logged_in", False):
    st.stop()

# Vanaf hier is gebruiker ingelogd
user = st.session_state.username

# --- Google Sheets authenticatie via Streamlit secrets ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = dict(st.secrets["google"])  # Hier gebruik je "google" als key in secrets.toml
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("zakgeld_data").sheet1

# Ophalen alle records en filter op ingelogde gebruiker
alle_records = sheet.get_all_records()
records = [r for r in alle_records if r.get("Gebruiker") == user]
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
st.markdown(f"**Ingelogd als:** {user}")
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
    st.warning("⚠️ Je hebt meer uitgegeven dan je inkomen! Bevestigen is niet mogelijk.")
    button_disabled = True
else:
    button_disabled = False

if st.button("✅ Bevestig deze week", disabled=button_disabled):
    rij = [
        user,  # Gebruiker
        week_id, inkomen, VASTE_KOSTEN_HUUR, VASTE_KOSTEN_ETEN,
        klusjes_verdiensten, gespaard, uitgegeven, over, cumulatief
    ]
    sheet.append_row(rij)
    st.success(f"Week {week_id} opgeslagen voor {user}!")
    st.balloons()

# Visualisatie overzicht
st.subheader("📈 Overzicht")

df = pd.DataFrame(records)

if not df.empty:
    st.write(f"📄 Gegevens voor gebruiker: {user}")

    # Zorg dat kolom Week ID bestaat en heet exact zo
    if "Week ID" not in df.columns and "Week" in df.columns:
        df.rename(columns={"Week": "Week ID"}, inplace=True)

    # Zet kolom Week ID als categorische variabele om correcte volgorde te houden
    df["Week ID"] = pd.Categorical(
        df["Week ID"],
        ordered=True,
        categories=sorted(
            df["Week ID"].unique(),
            key=lambda x: (
                int(x.split()[1].split("-")[0]),  # weeknummer
                int(x.split()[2])                 # jaar
            )
        )
    )

    # Altair grafiek inkomsten & uitgaven
    base = alt.Chart(df).encode(x=alt.X('Week ID:N', title='Week'))

    inkomsten_line = base.mark_line(color='green').encode(y='Inkomen:Q', tooltip=['Week ID', 'Inkomen'])
    huur_line = base.mark_line(color='red').encode(y='Huur:Q')
    eten_line = base.mark_line(color='orange').encode(y='Eten:Q')
    klusjes_line = base.mark_line(color='blue').encode(y='Klusjes:Q')
    uitgegeven_line = base.mark_line(color='purple').encode(y='Uitgegeven:Q')

    line_chart = alt.layer(
        inkomsten_line, huur_line, eten_line, klusjes_line, uitgegeven_line
    ).resolve_scale(y='independent').properties(
        width=700, height=350, title='Inkomsten en Uitgaven per Week'
    ).interactive()

    st.altair_chart(line_chart, use_container_width=True)

    # Cumulatief saldo grafiek
    cumulatief_chart = alt.Chart(df).mark_line(color='black').encode(
        x='Week ID:N',
        y='Totaal Over:Q',
        tooltip=['Week ID', 'Totaal Over']
    ).properties(
        width=700, height=350, title='Cumulatief Overgebleven Bedrag'
    ).interactive()

    st.altair_chart(cumulatief_chart, use_container_width=True)

    # Volledige tabel
    st.write("📄 Volledige gegevens")
    st.dataframe(df)
else:
    st.info("Er zijn nog geen gegevens om te tonen.")
