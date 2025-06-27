import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import altair as alt
from pathlib import Path

# 1) Page config + sanity check
st.set_page_config(page_title="💰 Zakgeld Spel", layout="centered")
st.write("🚀 App is starting…")

# 2) Locate & load credentials.txt
cred_path = Path(__file__).parent / "credentials.txt"
st.write(f"Looking for credentials.txt at: {cred_path}")
if not cred_path.exists():
    st.error("❌ credentials.txt niet gevonden! Plaats een bestand met `username,password` per regel naast app.py.")
    st.stop()

def load_users(filepath: Path):
    users = {}
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2:
            users[parts[0]] = parts[1]
    return users

USERS = load_users(cred_path)
st.write("✅ Loaded USERS:", list(USERS.keys()))

# 3) Login flow
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
                st.success(f"Welkom, {username}!")
                st.experimental_rerun()
            else:
                st.error("❌ Foutieve gebruikersnaam of wachtwoord")
        st.stop()

login()  # if not logged in, we stop here

# 4) From here on the user is authenticated
user = st.session_state.username
st.write(f"✅ Ingelogd als: {user}")

# 5) Google Sheets auth via streamlit secrets
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

# 6) Fetch past records
all_records = sheet.get_all_records()
records = [r for r in all_records if r.get("Gebruiker") == user]
prev_cum = records[-1]["Totaal Over"] if records else 0

# 7) Constants
ZAKGELD = 5
HUUR = 3
ETEN = 1

# 8) UI for new entry
st.title("💰 Zakgeld Spel")
today = date.today()
weeknum, year = today.isocalendar().week, today.year
week_id = f"Week {weeknum} - {year}"
st.markdown(f"**Huidige week:** {week_id}")

st.subheader("📋 Invoer voor deze week")
klusjes = st.number_input("Klusjes (€)", min_value=0, value=0)
gespaard = st.number_input("Sparen (€)", min_value=0, value=0)
uitgegeven = st.number_input("Uitgegeven (€)", min_value=0, value=0)

inkomen = ZAKGELD + klusjes
uitgaven = HUUR + ETEN + gespaard + uitgegeven
over = inkomen - uitgaven
cumul = prev_cum + over

if over < 0:
    st.warning("⚠️ Meer uitgegeven dan inkomen; bevestigen uitgeschakeld.")
    btn_disabled = True
else:
    btn_disabled = False

if st.button("✅ Bevestig", disabled=btn_disabled):
    row = [user, week_id, inkomen, HUUR, ETEN, klusjes, gespaard, uitgegeven, over, cumul]
    sheet.append_row(row)
    st.success("Opgeslagen! 🎉")
    st.balloons()
    st.experimental_rerun()

# 9) Overview
st.subheader("📈 Overzicht")
df = pd.DataFrame(records)
if df.empty:
    st.info("Nog geen data om te tonen.")
else:
    if "Week" in df.columns and "Week ID" not in df.columns:
        df.rename(columns={"Week": "Week ID"}, inplace=True)

    df["Week ID"] = pd.Categorical(
        df["Week ID"],
        ordered=True,
        categories=sorted(df["Week ID"].unique(), key=lambda x: (int(x.split()[1]), int(x.split()[2]))),
    )

    base = alt.Chart(df).encode(x="Week ID:N")
    chart = alt.layer(
        base.mark_line(color="green").encode(y="Inkomen:Q"),
        base.mark_line(color="red").encode(y="Huur:Q"),
        base.mark_line(color="orange").encode(y="Eten:Q"),
        base.mark_line(color="blue").encode(y="Klusjes:Q"),
        base.mark_line(color="purple").encode(y="Uitgegeven:Q"),
    ).resolve_scale(y="independent").properties(width=700, height=350)
    st.altair_chart(chart, use_container_width=True)

    cumul_chart = (
        alt.Chart(df).mark_line(color="black")
        .encode(x="Week ID:N", y="Totaal Over:Q")
        .properties(title="Cumulatief saldo", width=700, height=350)
    )
    st.altair_chart(cumul_chart, use_container_width=True)
    st.dataframe(df)
