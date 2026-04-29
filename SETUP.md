# Car Hunter — Setup Guide

## 1. Supabase (database)

1. Go to [supabase.com](https://supabase.com) → New project (free tier)
2. Open **SQL Editor** → paste `schema.sql` → Run
3. Go to **Project Settings → API** → copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`

## 2. Gemini API Key (free)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create key → copy it → `GEMINI_API_KEY`

## 3. GitHub repo

```bash
cd car-hunter
git init
git add .
git commit -m "init"
gh repo create car-hunter --private --push --source .
```

Add secrets to the repo:
- **Settings → Secrets → Actions** → add `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`

The scraper will now run daily at **10:00 AM IST** automatically.
Manual trigger: **Actions → Daily Car Scrape → Run workflow**

## 4. Streamlit Community Cloud (UI)

1. Go to [share.streamlit.io](https://share.streamlit.io) → New app
2. Connect your GitHub repo → set `app.py` as the entrypoint
3. **Advanced → Secrets** → paste:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "your-key"
GEMINI_API_KEY = "your-key"
```

4. Deploy → share the URL with yourself

## 5. Local dev

```bash
cp .env.example .env        # fill in your keys
pip install -r requirements.txt
playwright install chromium

python scrape.py             # run scraper once
streamlit run app.py         # open UI at localhost:8501
```

## Notes

- Deleted cars (`✕`) are soft-deleted — they won't reappear in future scrapes
- Same car on multiple sites → one row, sources merged, lowest price shown
- The hash deduplicates on: make + model + variant + year + color + transmission + kms(±5000)
- TeamBHP may 403 initially — crawl4ai fallback handles it with a real browser
- OLX uses crawl4ai (Playwright) because it's fully JS-rendered
