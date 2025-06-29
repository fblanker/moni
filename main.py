import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
import uuid
from supabase import create_client, Client

# 1) Pagina‐configuratie
st.set_page_config(page_title="💰 Zakgeld Spel", layout="centered")

# 2) Supabase configuratie
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3) Login‐flow
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Inloggen")
    login_type = st.radio("Inloggen als:", ["Ouder", "Kind"], horizontal=True)

    if login_type == "Ouder":
        email = st.text_input("Email ouder", key="login_email")
        password = st.text_input("Wachtwoord", type="password", key="login_pw")

        if st.button("Inloggen als ouder"):
            try:
                result = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if result.session:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.user_type = "ouder"
                    st.success(f"✅ Welkom, {email}!")
                    st.session_state["__rerun_id"] = str(uuid.uuid4())
                    st.stop()
                else:
                    st.error("❌ Ongeldige inloggegevens")
            except Exception as e:
                st.error(f"Login fout: {str(e)}")

    else:  # Kind login
        child_username = st.text_input("Gebruikersnaam kind")
        child_password = st.text_input("Wachtwoord", type="password")

        if st.button("Inloggen als kind"):
            if not child_username or not child_password:
                st.warning("Vul zowel gebruikersnaam als wachtwoord in.")
            else:
                login_email = f"{child_username}@moni.local"
                try:
                    result = supabase.auth.sign_in_with_password(
                        {"email": login_email, "password": child_password}
                    )
                    if result.session:
                        st.session_state.logged_in = True
                        st.session_state.user_email = login_email
                        st.session_state.user_type = "kind"
                        st.session_state.user_username = child_username
                        st.success(f"✅ Welkom terug, {child_username}!")
                        st.session_state["__rerun_id"] = str(uuid.uuid4())
                        st.stop()
                    else:
                        st.error("❌ Onjuiste inloggegevens")
                except Exception as e:
                    st.error(f"Fout bij inloggen: {str(e)}")

    st.stop()

user = st.session_state.user_email
st.write(f"🔓 Ingelogd als **{user}**")

# Nieuw: Beheerscherm voor ouders
if st.session_state.get("user_type") == "ouder":
    st.subheader("👨‍👩‍👧 Nieuw account aanmaken voor kind")

    child_username = st.text_input("Gebruikersnaam kind")
    child_password = st.text_input("Wachtwoord kind", type="password")
    child_name = st.text_input("Naam kind")

    if st.button("➕ Maak account aan"):
        if not child_username or not child_password or not child_name:
            st.warning("Vul naam, gebruikersnaam en wachtwoord in.")
        else:
            try:
                email_alias = f"{child_username}@moni.local"
                result = supabase.auth.sign_up(
                    {"email": email_alias, "password": child_password}
                )
                if result.user:
                    st.success(f"✅ Account aangemaakt voor {child_username}.")
                    supabase.table("kind_profielen").insert({
                        "ouder_email": user,
                        "kind_email": email_alias,
                        "gebruikersnaam": child_username,
                        "naam": child_name
                    }).execute()
                else:
                    st.error("❌ Account kon niet worden aangemaakt.")
            except Exception as e:
                st.error(f"Fout bij aanmaken account: {str(e)}")

    st.subheader("👨‍👧 Mijn kinderen")
    kinderen_response = supabase.table("kind_profielen").select("*").eq("ouder_email", user).execute()
    kinderen = kinderen_response.data or []

    if not kinderen:
        st.info("Je hebt nog geen kindaccounts toegevoegd.")
    else:
        kind_namen = {k['kind_email']: k['naam'] for k in kinderen}
        kind_options = list(kind_namen.items())
        selected_kind_email = st.selectbox("📂 Kies een kind om gegevens te bekijken:", kind_options, format_func=lambda x: x[1])
        user = selected_kind_email[0]  # overschrijf user met gekozen kindaccount
        st.info(f"Toon gegevens voor kind: {selected_kind_email[1]}")

# 4) Haal records op uit Supabase
response = supabase.table("zakgeld_data").select("*").eq("email", user).execute()
all_records = response.data or []

try:
    prev_balance = float(all_records[-1]["Totaal_Over"])
except (KeyError, ValueError, IndexError):
    prev_balance = 0

# 5) Constantes
ZAKGELD_PER_WEEK = 5
VASTE_KOSTEN_HUUR = 3
VASTE_KOSTEN_ETEN = 1
TOTALE_VASTE_KOSTEN = VASTE_KOSTEN_HUUR + VASTE_KOSTEN_ETEN

# 6) Invoer voor deze week
st.title("💰 Zakgeld Spel")
today = date.today()
weeknum, year = today.isocalendar().week, today.year
week_id = f"Week {weeknum} - {year}"

st.markdown(f"**Huidige week:** {week_id}")
st.markdown(f"**Zakgeld:** €{ZAKGELD_PER_WEEK}")
st.markdown(f"**Vaste lasten:** €{TOTALE_VASTE_KOSTEN}")

klusjes = st.number_input("Geld verdiend met klusjes (€)", min_value=0, value=0)
inkomen = ZAKGELD_PER_WEEK + klusjes
uitgaven = TOTALE_VASTE_KOSTEN
beschikbaar = prev_balance + (inkomen - uitgaven)

st.markdown(f"**Beschikbaar om op te nemen:** €{beschikbaar}")
opgenomen = st.number_input(
    "Geld opgenomen (€)",
    min_value=0,
    max_value=max(beschikbaar, 0),
    value=0,
)

new_balance = prev_balance + (inkomen - uitgaven) - opgenomen

btn_disabled = opgenomen > beschikbaar

if st.button("✅ Bevestig deze week", disabled=btn_disabled):
    row = {
        "email": user,
        "Week_ID": week_id,
        "Inkomen": inkomen,
        "Uitgaven": uitgaven,
        "Opgenomen": opgenomen,
        "Totaal_Over": new_balance
    }
    supabase.table("zakgeld_data").insert(row).execute()
    st.success("🎉 Week opgeslagen!")
    st.session_state["__rerun_id"] = str(uuid.uuid4())
    st.stop()

# 7) Overzicht & grafieken
st.subheader("📈 Overzicht")
df = pd.DataFrame(all_records)

if df.empty:
    st.info("Nog geen gegevens om te tonen.")
else:
    df.columns = df.columns.str.strip()

    if "Week" in df.columns and "Week_ID" not in df.columns:
        df.rename(columns={"Week": "Week_ID"}, inplace=True)

    for col in ["Inkomen", "Uitgaven", "Opgenomen", "Totaal_Over"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    import re
    def parse_week(x: str):
        m = re.match(r"Week\s+(\d+)\s*-\s*(\d+)", x)
        return (int(m[1]), int(m[2])) if m else (9999, 9999)

    if "Week_ID" in df.columns:
        cats = sorted(df["Week_ID"].unique(), key=parse_week)
        df["Week_ID"] = pd.Categorical(df["Week_ID"],
                                        ordered=True,
                                        categories=cats)
    else:
        st.warning("⚠️ Geen kolom 'Week_ID' gevonden, niet gesorteerd.")

    import altair as alt
    if "Week_ID" in df.columns:
        base = alt.Chart(df).encode(x="Week_ID:N")
        duo = alt.layer(
            base.mark_line(color="green").encode(y="Inkomen:Q"),
            base.mark_line(color="red").encode(y="Uitgaven:Q")
        ).properties(width=700, height=300,
                     title="Inkomen vs Uitgaven")
        st.altair_chart(duo, use_container_width=True)

        cum = alt.Chart(df).mark_line().encode(
            x="Week_ID:N", y="Totaal_Over:Q"
        ).properties(width=700, height=300,
                     title="Cumulatieve Stand")
        st.altair_chart(cum, use_container_width=True)

    st.subheader("📄 Volledige gegevens")
    st.dataframe(df)
