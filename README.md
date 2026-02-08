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
app_base_url = "https://YOUR-APP-NAME.streamlit.app"
```
> Streamlit Cloud does not read GitHub Actions secrets.

### 2) Email confirmation redirect
Supabase email confirmations will redirect to `localhost` unless you configure a public URL.

1. In Supabase, go to **Authentication → URL Configuration**.
2. Set **Site URL** to your Streamlit app URL (for example: `https://YOUR-APP-NAME.streamlit.app`).
3. Add the same URL to **Redirect URLs**.
4. Provide the URL to the app via `app_base_url` in Streamlit secrets (see above). This lets the app set `email_redirect_to` during sign-up.

### 3) Run the app
```bash
streamlit run app.py
```
