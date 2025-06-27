import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime

# 🔐 Google Sheets authenticatie via Streamlit secrets
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

# 📥 Vorige records ophalen
records = sheet.get_all_records()
vorige_cumulatief = records[-1]["Totaal Over"] if records else 0

# 📌 Instellingen
ZAKGELD_PER_WEEK = 5
VASTE_KOSTEN_HUUR = 3
VASTE_KOSTEN_ETEN = 1

st.title("💰 Zakgeld Spel")

# 📆 Week + jaar invoer
jaar = st.number_input("Jaar", min_value=2023, max_value=2100, value=datetime.now().year)
week = st.number_input("Weeknummer", min_value=1, max_value=53, value=datetime.no_
