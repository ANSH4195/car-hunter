# Changelog

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
