# 📁 moni/shared/supabase_client.py
from supabase import create_client
import streamlit as st

# Haal URL en API key uit Streamlit secrets
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]

# Maak de Supabase client aan
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Gebruik in andere scripts:
# from shared.supabase_client import get_supabase
# supabase = get_supabase()
