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
- **B3b** TeamBHP returns 403 on GitHub Actions (Azure IPs)
  - httpx → 403; crawl4ai fallback also blocked in <1s — pure IP-level block, no workaround without non-Azure IP
  - Options: (a) self-hosted runner, (b) residential proxy passed to httpx
---

## Planned

---

## Implemented

---

## Implemented

- **B3a** Cars24 + Spinny — rewrote both scrapers to pure httpx (no crawl4ai/Playwright):
  - Cars24: Next.js RSC endpoint (`RSC: 1` header) returns full listing JSON; `_extract_content()` finds the `content` array via `json.JSONDecoder.raw_decode`; supports `searchAfter` cursor pagination
  - Spinny: `api.spinny.com/v3/api/listing/v6/` REST API; luxury brands via `car_category=luxury`, non-luxury targets (VW/Skoda/Ford/Mitsubishi) via explicit `make=`+`model=` params
  - Confirmed locally: Cars24 → 24 listings, Spinny → 32 listings

---

## Verified

- **O4** TeamBHP: added Mitsubishi Pajero Sport (model ID 2812); fixed multi-word model name parsing; confirmed `restore=1` session pagination works correctly — full URL always returns page 1 regardless of `page=N`. ~20 → 52 listings/run.
- **O3** Carwale URL optimisation — switched VW/Skoda/Jeep/Ford to hyphenated `{make}-{model}` URLs (server-side model filter); added pagination for broad-make URLs (Audi/BMW/Mercedes/Volvo). ~33% fewer stocks fetched per run.
- **F3** UX: Source navigation click area
- **B2** 9thgear Gemini 429 rate limit — removed Gemini entirely from 9thgear; card text is pipe-delimited with fixed structure, all fields parsed directly
- **O1** Incremental scraping — load all existing IDs once at run start; skip upsert for known listings (~95% fewer DB writes); URL pre-filter for 9thgear/OLX skips parse for already-seen cards
- **O2** Reduce Gemini calls — `normalize()` and all Gemini code deleted from `normalizer.py`; no scraper calls Gemini anymore
