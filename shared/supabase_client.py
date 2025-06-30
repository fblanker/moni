from supabase import create_client
import streamlit as st

SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]

def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)