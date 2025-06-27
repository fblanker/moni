import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
from pathlib import Path

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
        u, p = [p.strip() for p in line.split(",")]
        users[u] = p
    return users

USERS = load_users(CRED_PATH)

# 3) Login‐flow (1 klik)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Inloggen")
    user_input = st.text_input("Gebruikersnaam", key="login_user")
    pw_input   = st.text_input("Wachtwoord", type="password", key="login_pw")
    if st.button("Inloggen"):
        if USERS.get(user_input) == pw_input:
            st.session_state.logged_in = True
            st.session_state.username  = user_input
            st.success(f"✅ Welkom, {user_input}!")
            st.experimental_rerun()
        else:
            st.error("❌ Foutieve gebruikersnaam of wachtwoord")
    st.stop()

user = st.session_state.username
st.write(f"🔓 Ingelogd als **{user}**")

# 4) Google Sheets authenticatie via secrets.toml
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

# 5) Haal alleen de relevante records op
all_records = sheet.get_all_records()  # verwacht geen dubbele headers meer
records = [r for r in all_records if r["Gebruiker"] == user]
prev_balance = records[-1]["Totaal Over"] if records else 0

# 6) Constantes
ZAKGELD_PER_WEEK  = 5
VASTE_KOSTEN_HUUR = 3
VASTE_KOSTEN_ETEN = 1
TOTALE_VASTE_KOSTEN = VASTE_KOSTEN_HUUR + VASTE_KOSTEN_ETEN

# 7) Invoer voor deze week
st.title("💰 Zakgeld Spel")
today = date.today()
weeknum, year = today.isocalendar().week, today.year
week_id = f"Week {weeknum} - {year}"

st.markdown(f"**Huidige week:** {week_id}")
st.markdown(f"**Zakgeld:** €{ZAKGELD_PER_WEEK}")
st.markdown(f"**Vaste lasten:** €{TOTALE_VASTE_KOSTEN}")

klusjes     = st.number_input("Geld verdiend met klusjes (€)", min_value=0, value=0)
inkomen     = ZAKGELD_PER_WEEK + klusjes
uitgaven    = TOTALE_VASTE_KOSTEN
beschikbaar = prev_balance + (inkomen - uitgaven)
st.markdown(f"**Beschikbaar om op te nemen:** €{beschikbaar}")

opgenomen = st.number_input(
    "Geld opgenomen (€)",
    min_value=0,
    max_value=max(beschikbaar, 0),
    value=0
)

new_balance = prev_balance + (inkomen - uitgaven) - opgenomen
if opgenomen > beschikbaar:
    st.warning("⚠️ Je kunt niet meer opnemen dan beschikbaar!")
    btn_disabled = True
else:
    btn_disabled = False

# Append‐row zonder “Uitgegeven”
if st.button("✅ Bevestig deze week", disabled=btn_disabled):
    row = [
        user,
        week_id,
        inkomen,
        uitgaven,
        opgenomen,
        new_balance,
    ]
    sheet.append_row(row)
    st.success("🎉 Week opgeslagen!")
    st.experimental_rerun()

# 8) Overzicht & grafieken
st.subheader("📈 Overzicht")
df = pd.DataFrame(records)

if df.empty:
    st.info("Nog geen gegevens om te tonen.")
else:
    # kolomnamen strippen en numeriek forceren
    df.columns = df.columns.str.strip()
    for col in ["Inkomen", "Uitgaven", "Opgenomen", "Totaal Over"]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # sorteer op weeknummer
    import re
    def parse_week(x: str):
        m = re.match(r"Week\s+(\d+)\s*-\s*(\d+)", x)
        return (int(m[1]), int(m[2])) if m else (9999, 9999)
    cats = sorted(df["Week ID"].unique(), key=parse_week)
    df["Week ID"] = pd.Categorical(df["Week ID"], ordered=True, categories=cats)

    # Chart: Inkomen vs Uitgaven
    import altair as alt
    base = alt.Chart(df).encode(x="Week ID:N")
    duo = alt.layer(
        base.mark_line(color="green").encode(y="Inkomen:Q"),
        base.mark_line(color="red").encode( y="Uitgaven:Q")
    ).properties(width=700, height=300, title="Inkomen vs Uitgaven")
    st.altair_chart(duo, use_container_width=True)

    # Cumulatieve stand
    cum = alt.Chart(df).mark_line().encode(
        x="Week ID:N", y="Totaal Over:Q"
    ).properties(width=700, height=300, title="Cumulatieve Stand")
    st.altair_chart(cum, use_container_width=True)

    st.subheader("📄 Volledige gegevens")
    st.dataframe(df)
