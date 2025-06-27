import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
from pathlib import Path
import altair as alt
import re

# 1) Pagina‐configuratie
st.set_page_config(page_title="💰 Zakgeld Spel", layout="centered")

# 2) Credentials inladen
CRED_PATH = Path(__file__).parent / "credentials.txt"
if not CRED_PATH.exists():
    st.error(f"❌ credentials.txt niet gevonden: {CRED_PATH}")
    st.stop()

def load_users(fp: Path) -> dict[str, str]:
    users = {}
    for line in fp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2:
            users[parts[0]] = parts[1]
    return users

USERS = load_users(CRED_PATH)

# 3) Login‐flow
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 Inloggen")
        username = st.text_input("Gebruikersnaam")
        password = st.text_input("Wachtwoord", type="password")
        if st.button("Inloggen"):
            if USERS.get(username) == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"✅ Welkom, {username}!")
                # geen st.stop() hier, zodat de rest direct gerund wordt
            else:
                st.error("❌ Foutieve gebruikersnaam of wachtwoord")
        st.stop()

login()
user = st.session_state.username
st.write(f"🔓 Ingelogd als **{user}**")

# 4) Google Sheets authenticatie
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]
creds_dict = dict(st.secrets["google"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("zakgeld_data").sheet1

# 5) Bestaande records ophalen
all_records = sheet.get_all_records()
records = [r for r in all_records if r.get("Gebruiker") == user]
prev_cumulative = records[-1]["Totaal Over"] if records else 0

# 6) Constantes
ZAKGELD = 5
HUUR = 3
ETEN = 1

# 7) Invoerveld: klusjes, uitgaven & opname
st.title("💰 Zakgeld Spel")
today = date.today()
weeknum, year = today.isocalendar().week, today.year
week_id = f"Week {weeknum} - {year}"

st.markdown(f"**Huidige week:** {week_id}")
st.markdown(f"**Zakgeld:** €{ZAKGELD}")
st.markdown(f"**Vaste lasten:** Huur €{HUUR}, Eten €{ETEN}")

st.subheader("📋 Invoer voor deze week")
klusjes    = st.number_input("Geld verdiend met klusjes (€)", min_value=0, value=0)
uitgegeven = st.number_input("Geld uitgegeven (€)",             min_value=0, value=0)

# 8) Berekeningen
inkomen    = ZAKGELD + klusjes
vaste      = HUUR + ETEN
# automatisch sparen van wat overblijft na vaste lasten en uitgaven
gespaard   = max(inkomen - vaste - uitgegeven, 0)
# hoeveel er beschikbaar is om op te nemen
beschikbaar_opnamen = prev_cumulative + gespaard

st.markdown(f"**Automatisch gespaard:** €{gespaard}")
st.markdown(f"**Beschikbaar om op te nemen:** €{beschikbaar_opnamen}")

opgenomen = st.number_input(
    "Geld opgenomen (€)",
    min_value=0,
    max_value=beschikbaar_opnamen,
    value=0
)

# na opname is de nieuwe cumulatieve stand:
new_cumul = prev_cumulative + gespaard - opgenomen

if opgenomen > beschikbaar_opnamen:
    st.warning("⚠️ Je kunt niet meer opnemen dan beschikbaar!")
    disable_btn = True
else:
    disable_btn = False

if st.button("✅ Bevestig deze week", disabled=disable_btn):
    row = [
        user,
        week_id,
        inkomen,
        HUUR,
        ETEN,
        klusjes,
        gespaard,
        uitgegeven,
        # over = wat er deze week ‘onbesteed’ bleef (hier altijd 0 door automatische besparing)
        0,
        # nieuw veld: opgenomen
        opgenomen,
        # totale stand na opname
        new_cumul,
    ]
    sheet.append_row(row)
    st.success("🎉 Week opgeslagen!")
    # de append_row triggert automatisch een rerun, zodat je nieuwe overzicht ziet

# 9) Overzicht & grafieken
st.subheader("📈 Overzicht")
df = pd.DataFrame(records)
if df.empty:
    st.info("Nog geen gegevens om te tonen.")
else:
    # Kolomnamen normaliseren
    if "Week" in df.columns and "Week ID" not in df.columns:
        df.rename(columns={"Week": "Week ID"}, inplace=True)

    # Robuuste sortering op Week ID
    def parse_week(x):
        m = re.match(r"Week\s+(\d+)\s*-\s*(\d+)", x)
        return (int(m[1]), int(m[2])) if m else (9999,9999)

    cats = sorted(df["Week ID"].unique(), key=parse_week)
    df["Week ID"] = pd.Categorical(df["Week ID"], ordered=True, categories=cats)

    base = alt.Chart(df).encode(x=alt.X("Week ID:N", title="Week"))
    lines = alt.layer(
        base.mark_line(color="green").encode(y="Inkomen:Q",    tooltip=["Week ID","Inkomen"]),
        base.mark_line(color="red").encode(y="Huur:Q"),
        base.mark_line(color="orange").encode(y="Eten:Q"),
        base.mark_line(color="blue").encode(y="Klusjes:Q"),
        base.mark_line(color="purple").encode(y="Uitgegeven:Q"),
    ).resolve_scale(y="independent").properties(
        width=700, height=350, title="Inkomsten & Uitgaven"
    )
    st.altair_chart(lines, use_container_width=True)

    cumul_chart = (
        alt.Chart(df)
        .mark_line(color="black")
        .encode(x="Week ID:N", y="Totaal Over:Q", tooltip=["Week ID","Totaal Over"])
        .properties(title="Cumulatieve Stand", width=700, height=350)
    )
    st.altair_chart(cumul_chart, use_container_width=True)

    st.subheader("📄 Volledige gegevens")
    st.dataframe(df)
