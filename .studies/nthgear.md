# 9thGear Scraper

## Approach
Plain httpx + BeautifulSoup + Gemini AI for card title normalization.

## Why httpx (not crawl4ai)
9thGear (`9thgear.co.in`) is a simple server-rendered site. Listing cards are fully present in the static HTML. No JavaScript rendering needed.

## URL Pattern
```
/search?fuel=Diesel&page={N}
```

Up to 4 pages per run. 9thGear is a small Bangalore-focused luxury used car dealer — the full diesel inventory across all makes fits within a few pages.

## Card Structure
```
div.main-car                          ← container (inside div.col-lg-3.col-md-3.col-sm-6)
  h3 > a                              ← title in ALL CAPS (e.g. "2019 AUDI Q7 3.0 TDI")
  span.posted_by                      ← price (₹ format)
  (text node matching \d+ km)         ← mileage
  a[href*="luxury-used-cars"]         ← listing URL
  img[src*="upload"]                  ← thumbnail
```

The title is ALL CAPS; `.title()` is applied to normalize casing before further processing.

## Why Gemini normalize()
9thGear titles are free-form strings like "2019 AUDI Q7 3.0 TDI QUATTRO TIPTRONIC" — there is no structured DOM for make, model, variant, year individually. Rather than building fragile regex parsers for every possible format, the title is passed to `normalizer.normalize()` which calls Gemini to extract structured fields (make, model, variant, year, fuel, transmission, color).

This is the only scraper that uses Gemini for card parsing. All other scrapers have structured DOM elements or known text patterns. 9thGear's unstructured titles make Gemini the pragmatic choice.

## Rate Limit
Gemini free tier: 5 requests/minute. 9thGear typically has 20–40 diesel cards across 4 pages, so the scraper may hit the rate limit and retry. The `normalize()` function in `normalizer.py` handles this with exponential backoff.

## Make Filtering
Before calling Gemini, a quick keyword check (`any(m in title.lower() for m in TARGET_MAKES)`) skips cards for non-target makes (e.g. Toyota, Honda). This reduces unnecessary Gemini calls.

## Known Limitations
- Gemini cost/latency: each card title is a separate API call. An in-memory cache by title string across cards in the same run would reduce duplicate calls (noted as a TODO optimization).
- 9thGear is Bangalore-only; location defaults to "Bangalore" for all listings.
