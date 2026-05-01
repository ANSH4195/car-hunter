# Car Hunter

Personal used car alert system for Karnataka. Scrapes Cars24, Spinny, OLX, Carwale, Cardekho, TeamBHP, and 9thgear daily and surfaces matching listings in a Streamlit dashboard.

**Target:** Diesel, Karnataka, 2017+, under 1.5 lakh km — Audi (any), BMW (any), Mercedes-Benz (any), Volvo (any), VW Tiguan, Skoda Octavia, Jeep Compass, Ford Endeavour

**Live app:** [car-hunter.streamlit.io](https://car-hunter.streamlit.io)

The scraper runs automatically every day at **10:00 AM IST** via GitHub Actions and pushes results to Supabase. The Streamlit UI reads from Supabase and lets you filter, sort, and dismiss listings.

---

## How it works

```
GitHub Actions (daily cron)
       │
       ▼
  scrape.py  ──►  7 scrapers (httpx + crawl4ai for JS-heavy sites)
       │
       ▼
  filters.py  ──►  drop anything that doesn't match criteria
       │
       ▼
  Supabase  ──►  upsert (same car on 2 sites = 1 row, sources merged)
       │
       ▼
  Streamlit  ──►  dashboard at share.streamlit.io
```

**Deduplication:** Each car is hashed on `make + model + variant + year + color + transmission + kms (bucketed to ±5000 km)`. The same physical car showing up on multiple platforms is collapsed into one row. The lowest price across sources is shown, and all source links are preserved as badges.

**Soft delete:** Clicking ✕ on a listing sets `is_active = false` in Supabase. The car won't reappear even if the scraper sees it again.

---

## Stack

| Layer | What |
|---|---|
| Scraping | `httpx` + `BeautifulSoup` for static pages, `crawl4ai` + Playwright for JS-rendered pages (OLX, TeamBHP fallback) |
| AI parsing | Gemini (free tier) for unstructured listing text |
| Database | Supabase (Postgres, free tier) |
| UI | Streamlit Community Cloud (free tier) |
| Automation | GitHub Actions cron — runs daily, no server needed |

---

## Setup

### 1. Supabase (database)

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** → paste the contents of `schema.sql` → Run
3. Go to **Project Settings → API** and copy:
   - **Project URL** → this is your `SUPABASE_URL`
   - **anon public** key → this is your `SUPABASE_KEY`

### 2. Gemini API key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create a key (free, no billing required) → copy it as `GEMINI_API_KEY`

### 3. GitHub Actions (daily scraper)

Add the three secrets to your repo:

**Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `SUPABASE_URL` | your Supabase project URL |
| `SUPABASE_KEY` | your Supabase anon key |
| `GEMINI_API_KEY` | your Gemini key |

The workflow at `.github/workflows/scrape.yml` will now run every day at 10 AM IST. You can also trigger it manually from the **Actions** tab → **Daily Car Scrape** → **Run workflow**.

### 4. Streamlit Community Cloud (dashboard)

1. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Connect this GitHub repo, set `app.py` as the entry point
3. Click **Advanced settings → Secrets** and paste:

```toml
SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"
SUPABASE_KEY = "your-anon-key"
GEMINI_API_KEY = "your-gemini-key"
```

4. Deploy — you'll get a public URL you can bookmark

### 5. Local dev

```bash
git clone https://github.com/ANSH4195/car-hunter
cd car-hunter

pip install -r requirements.txt
playwright install chromium

cp .env.example .env        # fill in your three keys

python scrape.py             # run scraper once
streamlit run app.py         # UI at http://localhost:8501
```

---

## Scrapers

| Source | Method | Notes |
|---|---|---|
| Cars24 | httpx + `__NEXT_DATA__` JSON | embedded in page HTML |
| Spinny | httpx + JSON | REST-like page data |
| Carwale | httpx + JSON | page props extraction |
| Cardekho | httpx + JSON | page props extraction |
| 9thgear | httpx + BeautifulSoup | HTML scrape |
| OLX | crawl4ai + Playwright | fully JS-rendered, needs real browser |
| TeamBHP | crawl4ai + Playwright | 403s on plain httpx, fallback to browser |

---

## Filters

Defined in `filters.py`. Current criteria:

- **Fuel:** Diesel only
- **Year:** 2017 or newer
- **Odometer:** under 1,50,000 km
- **Makes/models:**
  - Audi — any model
  - BMW — any model
  - Mercedes-Benz — any model
  - Volvo — any model
  - Volkswagen — Tiguan
  - Skoda — Octavia
  - Jeep — Compass *(pre-2022 must be Limited Plus variant)*
  - Ford — Endeavour

To change these, edit the constants at the top of `filters.py`.

---

## Customising for your search

**Change target cars** — edit `TARGET` dict in `filters.py` and the `MAKES` list in each scraper file.

**Change cities** — edit the `CITIES` list in each scraper (currently: Bangalore, Mysore, Mangalore, Hubli).

**Change scrape time** — edit the cron in `.github/workflows/scrape.yml` (currently `30 4 * * *` = 10 AM IST).

---

## Database schema

```sql
create table listings (
  id           text primary key,   -- sha256 hash of car identity
  make         text,
  model        text,
  variant      text,
  year         int,
  kms          int,
  fuel         text,
  transmission text,
  color        text,
  location     text,
  price        int,                -- lowest price seen (INR)
  image_url    text,
  sources      jsonb,              -- {"cars24": {"url": "...", "price": 4200000}, ...}
  first_seen   date,
  is_active    boolean
);
```
