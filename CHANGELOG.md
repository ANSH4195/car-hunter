# Changelog

## 2026-05-08
- Cars24: rewrote scraper from crawl4ai+Playwright to pure httpx; Next.js RSC endpoint (`RSC: 1` header) returns all listing JSON server-side — eliminates Azure IP bot-block that caused 0 results on GitHub Actions
- Spinny: rewrote scraper from crawl4ai+Playwright to direct REST API (`api.spinny.com/v3/api/listing/v6/`); luxury brands via `car_category=luxury`, non-luxury targets via explicit make+model params — also bypasses bot-block on Actions

## 2026-05-04 (3)
- TeamBHP: added Mitsubishi Pajero Sport model ID (2812) — previously zero listings captured from this source; fixed multi-word model name parsing so "Pajero Sport" is stored correctly; total listings per run increased from ~20 to ~52
- TeamBHP pagination confirmed working: `restore=1` session replay is necessary (full URL ignores `page=N` and always returns page 1); pagination kept as-is

## 2026-05-04 (2)
- Carwale: switched VW/Skoda/Jeep/Ford to hyphenated `{make}-{model}` URLs for server-side model filtering (~33% fewer stocks fetched); added full pagination for Audi/BMW/Mercedes/Volvo broad-make URLs so results beyond page 1 are no longer missed

## 2026-05-04
- Incremental scraping: load all existing listing IDs once at run start; skip upsert for already-seen listings (~95% fewer DB writes on steady-state runs)
- Added URL pre-filter for 9thgear and OLX: skip Gemini/parse entirely for cards whose source URL is already in the DB
- 9thgear: removed Gemini dependency entirely; card text is pipe-delimited with fixed structure so all fields (year, kms, price, make, model, variant) are now parsed directly — eliminates rate limit failures on this source
- Fixed Cardekho scraper missing from orchestrator (`scrape.py` was never calling it despite the scraper existing)

## 2026-05-02
- Redesigned card layout: mobile-first list view with clickable image modal, favicon source icons in right column, ellipsis popover for actions
- Added 3D chrome brand logos (Audi rings, BMW roundel, Volkswagen, Jeep wordmark) in listing titles instead of plain make text

## 2026-05-03
- Expanded scraping to Madhya Pradesh: Bhopal, Indore, Gwalior, Jabalpur across Cars24, Spinny, Carwale, CardDekho, OLX
- Added `state` field to listings (DB migration: `alter table listings add column if not exists state text;`)
- Added State filter in sidebar to view Karnataka vs Madhya Pradesh listings independently
- City/location now shown in each listing card

## 2026-05-01
- Rewrote TeamBHP scraper: plain httpx works (server-rendered); extracted MakeModel IDs from tree_MakeModel JS; session-based pagination; 51 unique listings
- Rewrote Cars24 scraper: crawl4ai on pre-filtered URL (f= syntax); was returning 0 (SSR shell has empty carList, data is client-rendered)
- Rewrote Spinny scraper: now uses crawl4ai to render the pre-filtered Spinny search URL, yielding 7 real listings (was 0)
- Fixed `parse_kms` to handle decimal+K format (e.g. "50.5K km" → 50500; was wrongly parsing to 5000)
- Added BMW, Mercedes-Benz, Volvo (any model) and Ford Endeavour across all 7 scrapers and filters
- Audi de-restricted to any model (was A3/Q3/Q5/Q7 only)
- OLX URL uses single-URL approach: blanket makes get all models, specific makes use model_eq filter


- Fixed OLX scraper: replaced 4 keyword search queries with a single pre-filtered Karnataka-wide URL, yielding actual target listings instead of zero results
- OLX mileage cap and year range now dynamically driven by `filters.py` constants
- Relaxed `MIN_YEAR` filter from 2019 → 2017 so older qualifying listings are stored (UI can still filter to 2019+)

## 2026-04-29
- Added "Not interested" (soft-delete) and "Delete" (hard-delete, re-fetches next run) buttons per listing, replacing the single dismiss button
- Default sort changed to "Newest first"; fixed sort direction bug (was sorting oldest first)
- Fixed 9thgear price parser picking up wrong value from HTML comment in card (Tiguan showed 9L instead of 21L)
