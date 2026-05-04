# Car Hunter — Claude Context

Personal used car alert system for Karnataka, India. Scrapes 7 Indian used car marketplaces daily for specific diesel vehicles, deduplicates listings, and displays them in a Streamlit dashboard.

## What it does
- Scrapes Cars24, Spinny, OLX, Carwale, Cardekho, TeamBHP, 9thgear daily via GitHub Actions (10 AM IST)
- Targets: Audi (any), BMW (any), Mercedes-Benz (any), Volvo (any), Volkswagen (Tiguan), Skoda (Octavia), Jeep (Compass), Ford (Endeavour), Mitsubishi (Pajero Sport) — diesel, 2017+, <150k km, Karnataka cities
- Deduplicates via SHA256 hash of make+model+variant+year+color+transmission+kms_bucket(±5k)
- Stores in Supabase (Postgres); shows in Streamlit with soft-delete

## Stack
- Python 3.11, httpx, BeautifulSoup, crawl4ai + Playwright (JS-heavy sites), Google Gemini API (AI parsing), Supabase, Streamlit

## Key Files
| File | Role |
|------|------|
| `app.py` | Streamlit UI — filters, sort, display, soft-delete |
| `scrape.py` | Orchestrator — runs all scrapers, filters, upserts to DB |
| `db.py` | Supabase ops — upsert, soft_delete, fetch_active |
| `filters.py` | Validation — TARGET dict, MIN_YEAR=2019, MAX_KMS=150000, FUEL=diesel |
| `normalizer.py` | Gemini AI parsing + regex helpers for price/kms |
| `schema.sql` | DB schema — single `listings` table |
| `scrapers/base.py` | `CarListing` dataclass + `listing_id()` dedup hash |
| `scrapers/*.py` | 7 scrapers (cars24, spinny, olx, teambhp, nthgear, carwale, cardekho) |
| `.github/workflows/scrape.yml` | Daily cron — `30 4 * * *` UTC = 10 AM IST |

## Scraping Strategies
| Site | Method |
|------|--------|
| Cars24, Spinny, Carwale, Cardekho | httpx + `__NEXT_DATA__` JSON embedded in HTML |
| 9thgear | httpx + BeautifulSoup |
| OLX | crawl4ai + Playwright (JS rendering) + Gemini parsing |
| TeamBHP | httpx with spoofed headers; crawl4ai fallback on 403 |

## Env Vars Required
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anon key
- `GEMINI_API_KEY` — Google AI Studio key (free tier)

## Run Locally
```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # fill in keys
python scrape.py       # run scraper
streamlit run app.py   # UI at localhost:8501
```

## Changelog
Maintain `CHANGELOG.md` in the repo root. Format: `## YYYY-MM-DD` header, bullet points. Only log significant changes (new features, bug fixes with user impact, schema changes) — not minor refactors or dependency bumps.

## Target Criteria (filters.py)
- Makes/Models: Audi A3/Q3/Q5/Q7, VW Tiguan, Skoda Octavia, Jeep Compass, Mitsubishi Pajero Sport
- Fuel: diesel only
- Year: >= 2019
- KMs: <= 150,000
- Special: Jeep Compass pre-2022 must be "Limited Plus" variant
- Cities: Bangalore, Mysore, Mangalore, Hubli

## Tooling Preferences
- Use `gh` (GitHub CLI) for all GitHub operations (PRs, issues, releases) — not raw `git` API calls or curl
- Use `pnpm` over `npm` or `yarn` for any JS/Node package management

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
