# OLX Pagination Gap

**Checked:** 2026-05-16

## Finding

The OLX scraper only fetches page 1 of results. OLX paginates at 40 cards/page and the
filtered search returns far more than one page.

| Region | Pages | Cards on last page | Estimated total |
|---|---|---|---|
| Karnataka | 10 | 30 | ~390 |
| Madhya Pradesh | 3 | 6 | ~86 |
| **Combined** | | | **~476** |

DB at time of check: **72 active OLX listings** — roughly **15% capture rate**.

## Root Cause

`scrapers/olx.py → scrape()` calls `_listing_url(slug)` once per state and fetches that
single URL. No loop over pages.

## Fix

Add a `page` counter loop inside `scrape()`. OLX uses `&page=N` query param. Stop when
the fetched page returns fewer than 40 cards (partial last page) or has no next-page link.

Rough sketch:

```python
page = 1
while True:
    url = _listing_url(cfg["slug"]) + f"&page={page}"
    html = asyncio.run(_fetch_rendered(url))
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select('[data-aut-id="itemBox2"]')
    if not cards:
        break
    for card in cards:
        ...  # existing parse logic
    if len(cards) < 40:
        break
    page += 1
```

## Notes

- OLX renders JS so each page request costs one Playwright browser launch via crawl4ai.
  Consider reusing the crawler instance across pages to reduce overhead.
- The URL filter already scopes by make/model/fuel/year/mileage/price, so extra pages
  are all relevant listings, not noise.
- DB also has 56 active listings from 2017–2018 that predate the current `MIN_YEAR=2019`
  filter — worth a cleanup pass separately.
