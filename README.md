# monopoly
Project to create a Streamlit Life Monopoly.

## Setup

### 1) Supabase credentials
Provide credentials with one of these options:

**Option A — Streamlit secrets (local)**
Create `.streamlit/secrets.toml` in the repo root:
```toml
supabase_url = "https://YOUR_PROJECT.supabase.co"
supabase_key = "YOUR_SUPABASE_ANON_KEY"
```

**Option B — Environment variables**
```bash
export SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
export SUPABASE_KEY="YOUR_SUPABASE_ANON_KEY"
```

**Streamlit Cloud**
If you deploy on Streamlit Cloud, add the same keys in **App Settings → Secrets**:
```toml
supabase_url = "https://YOUR_PROJECT.supabase.co"
supabase_key = "YOUR_SUPABASE_ANON_KEY"
```
> Streamlit Cloud does not read GitHub Actions secrets.

### 2) Run the app
```bash
streamlit run app.py
```
