# TODO

> Status columns: **Listed** → **Planned** → **Implemented** → **Verified**
> Tags: `F` = feature, `B` = bug, `O` = optimization

---

## Listed

- **F1** Add precarmart scraper
  - Covers Bengaluru, Mysuru, Mangaluru — all Karnataka target cities
  - JS-rendered (Next.js SPA); listings not in static HTML, need crawl4ai + Playwright (same as OLX)
  - URL pattern: `/best-used-diesel-[make]-cars-in-[city]` → 12 URLs (4 makes × 3 cities)
  - CSS selectors for listing cards unknown — need one local Playwright run to inspect rendered HTML
  - Wire up: add import + `("precarmart", precarmart.scrape)` to `scrape.py` SCRAPERS list
- **F2** UX: Add last fetched date
- **B1** Stale source links — due to deduplication, images may be updating but source links aren't; investigate and fix
- **O3** Carwale fetches 588 listings / run; investigate if a more specific URL filter (city + make) reduces the set without missing real matches
- **O4** TeamBHP pagination returns same rows for all pages (PHP session not persisting across page requests); investigate if `restore=1` requires a cookie that isn't being sent — or cap at page 1 since inventory is small

---

## Planned

---

## Implemented

---

## Verified

- **F3** UX: Source navigation click area
- **B2** 9thgear Gemini 429 rate limit — removed Gemini entirely from 9thgear; card text is pipe-delimited with fixed structure, all fields parsed directly
- **O1** Incremental scraping — load all existing IDs once at run start; skip upsert for known listings (~95% fewer DB writes); URL pre-filter for 9thgear/OLX skips parse for already-seen cards
- **O2** Reduce Gemini calls — `normalize()` and all Gemini code deleted from `normalizer.py`; no scraper calls Gemini anymore
