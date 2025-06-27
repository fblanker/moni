import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
from pathlib import Path
import altair as alt
import re

# 1) Pagina-configuratie
st.set_page_config(page_title="💰 Zakgeld Spel", layout="centered")

# 2) Credentials inladen
CRED_PATH = Path(__file__).parent / "credentials.txt"
if not CRED_PATH.exists():
    st.error(f"❌ credentials.txt niet gevonden: {CRED_PATH}")
    st.stop()

def load_users(fp: Path) -> dict[str,str]:
    users = {}
    for line in fp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        u, p = [p.strip() for p in line.split(",")]
        users[u] = p
    return users

USERS = load_users(CRED_PATH)

# 3) Login met 2x knopdruk
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "auth_clicks" not in st.session_state:
        st.session_state.auth_clicks = 0

    if not st.session_state.logged_in:
        st.title("🔐 Inloggen")
        username = st.text_input("Gebruikersnaam")
        password = st.text_input("Wachtwoord", type="password")

        if st.button("Inloggen"):
            st.session_state.auth_clicks += 1
            if st.session_state.auth_clicks == 1:
                st.info("Druk nogmaals op **Inloggen** om door te gaan.")
                st.stop()
            else:
                # tweede druk: pas nu valideren
                if USERS.get(username) == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"✅ Welkom, {username}!")
                    # geen st.stop() meer; script loopt door
                else:
                    st.error("❌ Foutieve gebruikersnaam of wachtwoord")
                    # reset klikken
                    st.session_state.auth_clicks = 0
                    st.stop()

        # blokkeer rest van pagina tot ingelogd
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

# 5) Bestaande records en vorige stand
all_records = sheet.get_all_records()
records = [r for r in all_records if r.get("Gebruiker") == user]
prev_balance = records[-1]["Totaal Over"] if records else 0

# 6) Constantes
ZAKGELD_PER_WEEK  = 5
VASTE_KOSTEN_HUUR = 3
VASTE_KOSTEN_ETEN = 1

# 7) Invoervelden
st.title("💰 Zakgeld Spel")
today = date.today()
weeknum, year = today.isocalendar().week, today.year
week_id = f"Week {weeknum} - {year}"

st.markdown(f"**Huidige week:** {week_id}")
st.markdown(f"**Zakgeld:** €{ZAKGELD_PER_WEEK}")
st.markdown(f"**Vaste lasten:** Huur €{VASTE_KOSTEN_HUUR}, Eten €{VASTE_KOSTEN_ETEN}")

st.subheader("📋 Invoer voor deze week")
klusjes    = st.number_input("Geld verdiend met klusjes (€)", min_value=0, value=0)
uitgegeven = st.number_input("Geld uitgegeven (€)",             min_value=0, value=0)

# beschikbaar om op te nemen is saldo_vorig + (inkomen - uitgaven)
inkomen  = ZAKGELD_PER_WEEK + klusjes
uitgaven = VASTE_KOSTEN_HUUR + VASTE_KOSTEN_ETEN + uitgegeven
beschikbaar = prev_balance + (inkomen - uitgaven)

st.markdown(f"**Beschikbaar om op te nemen:** €{beschikbaar}")

opgenomen = st.number_input(
    "Geld opgenomen (€)",
    min_value=0,
    max_value=max(beschikbaar, 0),
    value=0
)

# nieuwe cumulatieve stand
new_balance = prev_balance + (inkomen - uitgaven) - opgenomen

if opgenomen > beschikbaar:
    st.warning("⚠️ Je kunt niet meer opnemen dan beschikbaar!")
    btn_disabled = True
else:
    btn_disabled = False

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
    # na deze widget‐actie loopt Streamlit vanzelf opnieuw

# 8) Overzicht & grafieken
st.subheader("📈 Overzicht")
# kolomnamen in sheet moeten nu zijn:
# ["Gebruiker","Week ID","Inkomen","Uitgaven","Opgenomen","Totaal Over"]
df = pd.DataFrame(records)

if df.empty:
    st.info("Nog geen gegevens om te tonen.")
else:
    # sorteer Week ID
    def parse_week(x):
        m = re.match(r"Week\s+(\d+)\s*-\s*(\d+)", x)
        return (int(m[1]), int(m[2])) if m else (9999,9999)

    cats = sorted(df["Week ID"].unique(), key=parse_week)
    df["Week ID"] = pd.Categorical(df["Week ID"], ordered=True, categories=cats)

    # Chart: alleen inkomen & uitgaven
    base = alt.Chart(df).encode(x=alt.X("Week ID:N", title="Week"))
    duo = alt.layer(
        base.mark_line(color="green").encode(y=alt.Y("Inkomen:Q", title="€"), tooltip=["Week ID","Inkomen"]),
        base.mark_line(color="red")  .encode(y="Uitgaven:Q", tooltip=["Week ID","Uitgaven"])
    ).properties(width=700, height=350, title="Inkomen vs Uitgaven per Week")

    st.altair_chart(duo, use_container_width=True)

    # Cumulatieve stand
    cumc = (
        alt.Chart(df)
        .mark_line(color="black")
        .encode(x="Week ID:N", y=alt.Y("Totaal Over:Q", title="€"), tooltip=["Week ID","Totaal Over"])
        .properties(width=700, height=350, title="Cumulatieve Stand")
    )
    st.altair_chart(cumc, use_container_width=True)

    st.subheader("📄 Volledige gegevens")
    st.dataframe(df)
