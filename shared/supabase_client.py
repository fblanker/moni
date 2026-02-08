from supabase import create_client
import os
from typing import Optional
import streamlit as st


def _normalize_supabase_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    cleaned = url.strip()
    if cleaned and not cleaned.startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"
    return cleaned


def _get_supabase_credentials():
    secrets = st.secrets if hasattr(st, "secrets") else {}
    url = (
        secrets.get("supabase_url")
        or secrets.get("SUPABASE_URL")
        or os.getenv("SUPABASE_URL")
    )
    key = (
        secrets.get("supabase_key")
        or secrets.get("SUPABASE_KEY")
        or os.getenv("SUPABASE_KEY")
    )
    return _normalize_supabase_url(url), key.strip() if key else None


def get_app_base_url() -> Optional[str]:
    secrets = st.secrets if hasattr(st, "secrets") else {}
    url = (
        secrets.get("app_base_url")
        or secrets.get("APP_BASE_URL")
        or os.getenv("APP_BASE_URL")
    )
    return _normalize_supabase_url(url)


def attach_supabase_session(supabase) -> None:
    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if access_token and refresh_token:
        try:
            supabase.auth.set_session(access_token, refresh_token)
        except Exception:
            pass


@st.cache_resource(show_spinner=False)
def get_supabase():
    url, key = _get_supabase_credentials()
    if not url or not key:
        raise RuntimeError(
            "Supabase credentials ontbreken. Voeg 'supabase_url' en 'supabase_key' "
            "toe aan Streamlit secrets (of gebruik SUPABASE_URL/SUPABASE_KEY). "
            "Let op: Streamlit Cloud leest geen GitHub Actions secrets."
        )
    return create_client(url, key)
