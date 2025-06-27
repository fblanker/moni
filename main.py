import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
from pathlib import Path
import altair as alt

# 1) Page config & startup message
st.set_page_config(page_title="💰 Zakgeld Spel", layout="centered")
st.write("🚀 App is starting…")

# 2) Locate & load credentials.txt
credentials_path = Path(__file__).parent / "credentials.txt"
st.write(f"🔑 Looking for credentials at: {credentials_path}")
if not credentials_path.exists():
    st.error(f"❌ credentials.txt not found at {credentials_path}")
    st.stop()

def load_users(filepath: Path) -> dict:
    users = {}
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2:
            users[parts[0]] = parts[1]
    return users

USERS = load_users(credentials_path)
st.write("✅ Loaded users:", list(USERS.keys()))

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
                st.info("🔄 Herlaad de pagina om door te gaan.")
            else:
                st.error("❌ Foutieve gebruikersnaam of wachtwoord")
        st.stop()

login()  # Halts here until credentials are correct

# 4) Authenticated user
user = st.session_state.username
st.write(f"✅ Ingelogd als: {user}")

# 5) Google Sheets auth via Streamlit secrets
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

# 6) Fetch existing records for this user
all_records = sheet.get_all_records()
records = [r for r in all_records if r.get("Gebruiker") == user]
previous_cumulative = records[-1]["Totaal Over"] if records else 0

# 7) Constants
ZAKGELD_PER_WEEK = 5
VASTE_KOSTEN_HUUR = 3
VASTE_KOSTEN_ETEN = 1

# 8) Input form for this week
st.title("💰 Zakgeld Spel")
today = date.today()
weeknum, year = today.isocalendar().week, today.year
week_id = f"Week {weeknum} - {year}"

st.markdown(f"**Huidige week:** {week_id}")
st.markdown(f"**Ingelogd als:** {user}")
st.markdown(f"**Zakgeld:** €{ZAKGELD_PER_WEEK}")
st.markdown(f"**Vaste lasten:** Huur €{VASTE_KOSTEN_HUUR} + Eten €{VASTE_KOSTEN_ETEN}")

st.subheader("📋 Invoer voor deze week")
klusjes = st.number_input("Geld verdiend met klusjes (€)", min_value=0, value=0)
gespaard = st.number_input("Geld om te sparen (€)", min_value=0, value=0)
uitgegeven = st.number_input("Geld uitgegeven (€)", min_value=0, value=0)

inkomen = ZAKGELD_PER_WEEK + klusjes
uitgaven = VASTE_KOSTEN_HUUR + VASTE_KOSTEN_ETEN + gespaa rd + uitgegeven
over = inkomen - uitgaven
cumulatief = previous_cumulative + over

if over < 0:
    st.warning("⚠️ Je hebt meer uitgegeven dan je inkomen! Bevestigen is niet mogelijk.")
    btn_disabled = True
else:
    btn_disabled = False

if st.button("✅ Bevestig deze week", disabled=btn_disabled):
    row = [
        user,
        week_id,
        inkomen,
        VASTE_KOSTEN_HUUR,
        VASTE_KOSTEN_ETEN,
        klusjes,
        gespaard,
        uitgegeven,
        over,
        cumulatief,
    ]
    sheet.append_row(row)
    st.success("✅ Opgeslagen! 🎉")
    # Try rerun or ask user to refresh
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st.info("🔄 Herlaad de pagina om de nieuwste data te zien.")
        st.stop()

# 9) Visualization & history
st.subheader("📈 Overzicht")
df = pd.DataFrame(records)
if df.empty:
    st.info("Er zijn nog geen gegevens om te tonen.")
else:
    if "Week" in df.columns and "Week ID" not in df.columns:
        df.rename(columns={"Week": "Week ID"}, inplace=True)

    df["Week ID"] = pd.Categorical(
        df["Week ID"],
        ordered=True,
        categories=sorted(
            df["Week ID"].unique(),
            key=lambda x: (int(x.split()[1]), int(x.split()[2])),
        ),
    )

    base = alt.Chart(df).encode(x=alt.X("Week ID:N", title="Week"))
    layered = alt.layer(
        base.mark_line(color="green").encode(y="Inkomen:Q", tooltip=["Week ID", "Inkomen"]),
        base.mark_line(color="red").encode(y="Huur:Q"),
        base.mark_line(color="orange").encode(y="Eten:Q"),
        base.mark_line(color="blue").encode(y="Klusjes:Q"),
        base.mark_line(color="purple").encode(y="Uitgegeven:Q"),
    ).resolve_scale(y="independent").properties(width=700, height=350, title="Inkomsten & Uitgaven")

    st.altair_chart(layered, use_container_width=True)

    cumul_chart = (
        alt.Chart(df)
        .mark_line(color="black")
        .encode(x="Week ID:N", y="Totaal Over:Q", tooltip=["Week ID", "Totaal Over"])
        .properties(width=700, height=350, title="Cumulatief Overgebleven Bedrag")
    )
    st.altair_chart(cumul_chart, use_container_width=True)

    st.subheader("📄 Volledige gegevens")
    st.dataframe(df)
