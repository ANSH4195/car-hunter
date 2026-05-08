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
- **B3** Cars24, Spinny, TeamBHP return 0 cards on GitHub Actions (Azure IPs)
  - All three scrapers work locally but fail on every scheduled/dispatched run since at least 2026-05-03
  - Cars24/Spinny use crawl4ai + Playwright (`[class*="carCardWrapper"]` / `.CarListingCardV2__carListingCardV2Root`); locally both selectors find 3+ cards, Actions finds 0 — page likely renders a captcha/geo-block for Azure IPs
  - TeamBHP httpx returns 403; crawl4ai fallback added (commit d4b0a32) but also gets blocked — fetches in <1s with no JS rendering on Actions
  - DB still has 10 Cars24, 5 Spinny, 3 TeamBHP listings from earlier runs when scrapers worked
  - Attempted: `simulate_user=True, magic=True` on crawl4ai — no effect (crawl4ai 0.4.247 pinned in requirements-scrape.txt; >=0.8.0 conflicts with streamlit==1.35.0 over pillow)
  - Next steps to try: (a) residential/datacenter proxy for GitHub Actions, (b) self-hosted runner on a non-cloud IP, (c) check if Cars24/Spinny expose a JSON API endpoint that bypasses the bot check
---

## Planned

---

## Implemented

---

## Verified

- **O4** TeamBHP: added Mitsubishi Pajero Sport (model ID 2812); fixed multi-word model name parsing; confirmed `restore=1` session pagination works correctly — full URL always returns page 1 regardless of `page=N`. ~20 → 52 listings/run.
- **O3** Carwale URL optimisation — switched VW/Skoda/Jeep/Ford to hyphenated `{make}-{model}` URLs (server-side model filter); added pagination for broad-make URLs (Audi/BMW/Mercedes/Volvo). ~33% fewer stocks fetched per run.
- **F3** UX: Source navigation click area
- **B2** 9thgear Gemini 429 rate limit — removed Gemini entirely from 9thgear; card text is pipe-delimited with fixed structure, all fields parsed directly
- **O1** Incremental scraping — load all existing IDs once at run start; skip upsert for known listings (~95% fewer DB writes); URL pre-filter for 9thgear/OLX skips parse for already-seen cards
- **O2** Reduce Gemini calls — `normalize()` and all Gemini code deleted from `normalizer.py`; no scraper calls Gemini anymore
