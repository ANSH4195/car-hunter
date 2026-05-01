# Changelog

## 2026-05-01
- Fixed OLX scraper: replaced 4 keyword search queries with a single pre-filtered Karnataka-wide URL, yielding actual target listings instead of zero results
- OLX mileage cap and year range now dynamically driven by `filters.py` constants
- Relaxed `MIN_YEAR` filter from 2019 → 2017 so older qualifying listings are stored (UI can still filter to 2019+)

## 2026-04-29
- Added "Not interested" (soft-delete) and "Delete" (hard-delete, re-fetches next run) buttons per listing, replacing the single dismiss button
- Default sort changed to "Newest first"; fixed sort direction bug (was sorting oldest first)
- Fixed 9thgear price parser picking up wrong value from HTML comment in card (Tiguan showed 9L instead of 21L)
