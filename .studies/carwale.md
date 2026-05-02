# CarWale Scraper

## Approach
Plain httpx + JSON extraction from `window.__INITIAL_STATE__` embedded in the server-rendered HTML.

## Why httpx (not crawl4ai)
CarWale server-renders its listing pages and embeds all listing data as a JSON blob assigned to `window.__INITIAL_STATE__` inside a `<script>` tag. This is a standard Next.js/SSR pattern where the page ships its full data payload for client-side hydration. We can parse the JSON directly from the raw HTML without needing a browser.

## URL Pattern
```
/used/{city}/{make}/
```

The scraper iterates over 4 cities × 8 makes = 32 URLs per run:

- Cities: `bangalore`, `mysore`, `mangalore`, `hubli`
- Makes: `audi`, `bmw`, `mercedes-benz`, `volkswagen`, `skoda`, `jeep`, `ford`, `volvo`

There's no fuel filter in the URL — CarWale's URL structure doesn't support it. Diesel filtering happens in code: `_to_listing()` skips any stock entry where `fuel != "diesel"`.

## Data Extraction
```python
idx = html.find("window.__INITIAL_STATE__ = {")
# walk forward matching braces to find the end of the JSON object
data["usedSearch"]["stocks"]  # list of listing dicts
```

Each stock dict contains structured fields: `makeName`, `rootName` (model), `versionName` (variant), `makeYear`, `kmNumeric`, `priceNumeric`, `transmission`, `fuel`, `cityName`, image URLs, and a relative listing URL.

## Known Limitations
- Each URL returns ~28 results (one page). No pagination is implemented — CarWale's `__INITIAL_STATE__` only includes the first page of results, and subsequent pages require client-side navigation that would need crawl4ai.
- This produces ~292 candidate stock entries per run (32 URLs × ~9 non-diesel skipped + ~19 diesel), of which roughly 40–60 pass the `filters.py` criteria.
- Model filtering (e.g. "only Tiguan for VW") is handled post-fetch by `scrape.py`'s `is_target()` check, not at the URL level.
