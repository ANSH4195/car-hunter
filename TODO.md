# TODO

- Add precarmart scraper
  - Covers Bengaluru, Mysuru, Mangaluru — all Karnataka target cities
  - JS-rendered (Next.js SPA); listings not in static HTML, need crawl4ai + Playwright (same as OLX)
  - URL pattern: `/best-used-diesel-[make]-cars-in-[city]` → 12 URLs (4 makes × 3 cities)
  - CSS selectors for listing cards unknown — need one local Playwright run to inspect rendered HTML
  - Parse with BeautifulSoup; fall back to Gemini `normalize()` where selectors fail
  - Wire up: add import + `("precarmart", precarmart.scrape)` to `scrape.py` SCRAPERS list
- Enable Cars24, Spinny scrapers (currently disabled)
- UX: Due to deduplication, images may be updating but source links aren't — investigate and fix stale link behaviour
- UX: Add last fetched date
- UX: Source navigation click area
