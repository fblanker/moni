from supabase import create_client
import os
import streamlit as st


def _get_supabase_credentials():
    secrets = st.secrets if hasattr(st, "secrets") else {}
    url = secrets.get("supabase_url") or os.getenv("SUPABASE_URL")
    key = secrets.get("supabase_key") or os.getenv("SUPABASE_KEY")
    return url, key


@st.cache_resource(show_spinner=False)
def get_supabase():
    url, key = _get_supabase_credentials()
    if not url or not key:
        raise RuntimeError(
            "Supabase credentials ontbreken. Voeg 'supabase_url' en 'supabase_key' "
            "toe aan Streamlit secrets of stel SUPABASE_URL/SUPABASE_KEY in."
        )
    return create_client(url, key)
