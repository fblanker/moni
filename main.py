import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import altair as alt

# --- Load users from external txt file ---
def load_users(filepath="credentials.txt"):
    users = {}
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) == 2:
                    username, pwd = parts
                    users[username] = pwd
    except FileNotFoundError:
        st.error(f"Credentials file not found: {filepath}")
        st.stop()
    return users

USERS = load_users()

# --- Login function ---
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

# Run login flow
login()

# From here on, user is authenticated
user = st.session_state.username

# --- Google Sheets setup via Streamlit secrets ---
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

# Fetch and filter
all_records = sheet.get_all_records()
records = [r for r in all_records if r.get("Gebruiker") == user]
prev_cumulative = records[-1]["Totaal Over"] if records else 0

# Constants
ZAKGELD_PER_WEEK = 5
VASTE_KOSTEN_HUUR = 3
VASTE_KOSTEN_ETEN = 1

# --- UI ---
st.title("💰 Zakgeld Spel")
today = date.today()
weeknum = today.isocalendar().week
year = today.year
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
uitgaven = VASTE_KOSTEN_HUUR + VASTE_KOSTEN_ETEN + gespaard + uitgegeven
over = inkomen - uitgaven
cumulatief = prev_cumulative + over

button_disabled = over < 0
if over < 0:
    st.warning("⚠️ Je hebt meer uitgegeven dan je inkomen! Bevestigen is niet mogelijk.")

if st.button("✅ Bevestig deze week", disabled=button_disabled):
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
    st.success(f"Week {week_id} opgeslagen voor {user}!")
    st.balloons()

# --- Visualization ---
st.subheader("📈 Overzicht")
df = pd.DataFrame(records)
if df.empty:
    st.info("Er zijn nog geen gegevens om te tonen.")
else:
    # Ensure consistent column names
    if "Week" in df.columns and "Week ID" not in df.columns:
        df = df.rename(columns={"Week": "Week ID"})
    df["Week ID"] = pd.Categorical(
        df["Week ID"],
        ordered=True,
        categories=sorted(
            df["Week ID"].unique(),
            key=lambda x: (int(x.split()[1]), int(x.split()[2])),
        ),
    )

    base = alt.Chart(df).encode(x=alt.X("Week ID:N", title="Week"))
    lines = alt.layer(
        base.mark_line(color="green").encode(y="Inkomen:Q", tooltip=["Week ID", "Inkomen"]),
        base.mark_line(color="red").encode(y="Huur:Q"),
        base.mark_line(color="orange").encode(y="Eten:Q"),
        base.mark_line(color="blue").encode(y="Klusjes:Q"),
        base.mark_line(color="purple").encode(y="Uitgegeven:Q"),
    ).resolve_scale(y="independent").properties(width=700, height=350)

    st.altair_chart(lines, use_container_width=True)

    cumul_chart = (
        alt.Chart(df)
        .mark_line(color="black")
        .encode(x="Week ID:N", y="Totaal Over:Q", tooltip=["Week ID", "Totaal Over"])
        .properties(width=700, height=350, title="Cumulatief Overgebleven Bedrag")
    )
    st.altair_chart(cumul_chart, use_container_width=True)

    st.subheader("📄 Volledige gegevens")
    st.dataframe(df)
