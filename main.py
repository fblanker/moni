import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
from pathlib import Path
import altair as alt
import re

# 1) Page config
st.set_page_config(page_title="💰 Zakgeld Spel", layout="centered")

# 2) Load credentials.txt
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

# 3) Simple login – no manual rerun needed
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
                # do NOT call st.stop() here so that
                # the script reruns immediately with logged_in=True
            else:
                st.error("❌ Foutieve gebruikersnaam of wachtwoord")
        st.stop()  # freeze everything until successful login

login()
user = st.session_state.username
st.write(f"🔓 Ingelogd als **{user}**")

# 4) Google Sheets auth via secrets
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

# 5) Fetch past records
all_records = sheet.get_all_records()
records = [r for r in all_records if r.get("Gebruiker") == user]
prev_cum = records[-1]["Totaal Over"] if records else 0

# 6) Constants
ZAKGELD = 5
HUUR = 3
ETEN = 1

# 7) Input form
st.title("💰 Zakgeld Spel")
today = date.today()
weeknum, year = today.isocalendar().week, today.year
week_id = f"Week {weeknum} - {year}"

st.markdown(f"**Huidige week:** {week_id}")
st.markdown(f"**Zakgeld:** €{ZAKGELD}")
st.markdown(f"**Vaste lasten:** Huur €{HUUR}, Eten €{ETEN}")

st.subheader("📋 Invoer voor deze week")
klusjes    = st.number_input("Geld verdiend met klusjes (€)", min_value=0, value=0)
gespaard   = st.number_input("Geld om te sparen (€)",       min_value=0, value=0)
uitgegeven = st.number_input("Geld uitgegeven (€)",         min_value=0, value=0)

inkomen    = ZAKGELD + klusjes
uitgaven   = HUUR + ETEN + gespaar d + uitgegeven
over       = inkomen - uitgaven
cumul      = prev_cum + over

if over < 0:
    st.warning("⚠️ Te veel uitgegeven! Opslaan uitgeschakeld.")
    disable_btn = True
else:
    disable_btn = False

if st.button("✅ Bevestig deze week", disabled=disable_btn):
    row = [user, week_id, inkomen, HUUR, ETEN,
           klusjes, gespaard, uitgegeven, over, cumul]
    sheet.append_row(row)
    st.success("🎉 Opgeslagen!")
    # Streamlit will automatically rerun on this widget-action
    # so the new row shows up in the overview below

# 8) Visualization & history
st.subheader("📈 Overzicht")
df = pd.DataFrame(records)

if df.empty:
    st.info("Nog geen gegevens om te tonen.")
else:
    # normalize column name
    if "Week" in df.columns and "Week ID" not in df.columns:
        df.rename(columns={"Week": "Week ID"}, inplace=True)

    # robust sort key: invalid IDs go to the end
    def parse_week_id(x: str) -> tuple[int,int]:
        m = re.match(r"Week\s+(\d+)\s*-\s*(\d+)", x)
        if m:
            return int(m.group(1)), int(m.group(2))
        return (9999, 9999)

    cats = sorted(df["Week ID"].unique(), key=parse_week_id)
    df["Week ID"] = pd.Categorical(df["Week ID"], ordered=True, categories=cats)

    base = alt.Chart(df).encode(x=alt.X("Week ID:N", title="Week"))
    lines = alt.layer(
        base.mark_line(color="green").encode(y="Inkomen:Q",    tooltip=["Week ID","Inkomen"]),
        base.mark_line(color="red").encode(y="Huur:Q"),
        base.mark_line(color="orange").encode(y="Eten:Q"),
        base.mark_line(color="blue").encode(y="Klusjes:Q"),
        base.mark_line(color="purple").encode(y="Uitgegeven:Q"),
    ).resolve_scale(y="independent").properties(width=700, height=350)

    st.altair_chart(lines, use_container_width=True)

    cumul_chart = (
        alt.Chart(df)
        .mark_line(color="black")
        .encode(x="Week ID:N", y="Totaal Over:Q", tooltip=["Week ID","Totaal Over"])
        .properties(title="Cumulatief Overgebleven Bedrag", width=700, height=350)
    )
    st.altair_chart(cumul_chart, use_container_width=True)

    st.subheader("📄 Volledige gegevens")
    st.dataframe(df)
