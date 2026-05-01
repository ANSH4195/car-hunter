# TODO

- Add precarmart scraper
  - Covers Bengaluru, Mysuru, Mangaluru — all Karnataka target cities
  - JS-rendered (Next.js SPA); listings not in static HTML, need crawl4ai + Playwright (same as OLX)
  - URL pattern: `/best-used-diesel-[make]-cars-in-[city]` → 12 URLs (4 makes × 3 cities)
  - CSS selectors for listing cards unknown — need one local Playwright run to inspect rendered HTML
  - Parse with BeautifulSoup; fall back to Gemini `normalize()` where selectors fail
  - Wire up: add import + `("precarmart", precarmart.scrape)` to `scrape.py` SCRAPERS list
- Scraper optimisation
  - Incremental scraping: track `last_scraped` timestamp per source in Supabase; only fetch/upsert listings newer than that date where the source supports sorting by newest (Cars24, OLX, Carwale already sort by newest/bestmatch — stop early when listing date < last_scraped)
  - Reduce Gemini calls: 9thgear currently calls `normalize()` on every card; cache results by title string so the same car title across runs doesn't hit the API again (in-memory dict per run is enough)
  - Carwale fetches 292 listings / run; investigate if a more specific URL filter (city + make) reduces the set without missing real matches
  - TeamBHP pagination returns same 20 rows for all pages (PHP session not persisting across page requests); investigate if `restore=1` requires a cookie that isn't being sent — or cap at page 1 since inventory is small
- UX: Due to deduplication, images may be updating but source links aren't — investigate and fix stale link behaviour
- UX: Add last fetched date
- UX: Source navigation click area
