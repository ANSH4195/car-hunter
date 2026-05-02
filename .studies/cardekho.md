# CarDekho Scraper

## Approach
Plain httpx + BeautifulSoup parsing of server-rendered HTML.

## Why httpx (not crawl4ai)
CarDekho's used-car search pages are server-rendered. The listing cards (`.NewUcExCard`) are present in the raw HTML response — no JavaScript execution required.

## URL Pattern
```
/used-cars/used-{Make}-cars-in-karnataka?fuel=Diesel&page={N}
```

The scraper iterates over 8 makes, up to 3 pages each (24 requests per run). The `fuel=Diesel` parameter is applied at the URL level, so no post-fetch fuel filtering is needed. Geography is Karnataka-wide (not city-specific) — city filtering happens later via `scrape.py`'s location check.

## Card Structure
```
div.NewUcExCard                        ← container
  .titlebox h3                         ← "2019 Audi Q5 2.0 TDI Technology" (year + make + model + variant)
  [class*="price"]                     ← price text (₹ format)
  (card text)                          ← "X kms • Diesel • Automatic"
  [class*="location"] or [class*="city"]  ← city name
  a[href*="used-car-details"]          ← listing URL
  img[data-src or src]                 ← thumbnail (lazy-loaded, prefer data-src)
```

Year is parsed from the title with regex. Make and model are the first two tokens of the title after the year is removed. Variant is the remaining tokens.

## Known Limitations
- CarDekho does not consistently expose transmission on all cards; the text-search fallback (`"Automatic" in card_text`) works for most listings.
- Image URLs are often in `data-src` (lazy-loaded) rather than `src`; the scraper checks both.
- Model filtering (e.g. Tiguan-only for VW) is not applied at the URL level — CarDekho's URL structure only supports make-level filtering. Post-fetch filtering in `scrape.py` handles this.
