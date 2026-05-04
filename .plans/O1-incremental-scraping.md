# O1 — Incremental Scraping

**Goal:** Only process listings not already in DB, avoiding redundant upserts and Gemini calls.

## Problem

Every run fetches all N listings from each source and upserts each one individually (SELECT + INSERT/UPDATE per listing). If 30 of 35 listings are unchanged from yesterday, we still do 30 wasted DB round trips and, for 9thgear, 30 wasted Gemini calls.

## Approach

Two layers, applied in order within each scraper run.

---

### Layer 1 — ID-set dedup (all sources)

Load all existing listing IDs into a set once before the scraper loop starts:

```python
# scrape.py main()
existing_ids = db.fetch_all_ids()  # SELECT id FROM listings
```

After parsing each source's listings, filter before upserting:

```python
new = [l for l in valid if l.listing_id() not in existing_ids]
for car in new:
    db.upsert(car)
```

**What this saves:** Eliminates redundant DB upserts for already-seen listings. One batch read replaces N individual SELECTs.

**Schema change:** None. `listing_id()` is already the PK.

**New DB function needed:** `db.fetch_all_ids() -> set[str]`

---

### Layer 2 — URL pre-filter for Gemini scrapers (9thgear, OLX)

`listing_id()` requires a full parse — which for 9thgear/OLX means calling Gemini first. So Layer 1 can't save Gemini calls; we need a pre-parse filter.

Each card has a source URL that's extractable before `normalize()`. The `sources` JSONB already stores `{source_name: {url: ..., price: ...}}` so all seen URLs are already in the DB.

Before the scraper loop for a Gemini-heavy source, load seen URLs:

```python
# in nthgear.scrape() and olx.scrape()
seen_urls = db.fetch_source_urls("9thgear")  # set[str]
```

In the card-parsing loop, skip Gemini if URL already seen:

```python
url = extract_url(card)   # cheap, no Gemini
if url in seen_urls:
    continue
listing = _parse_card(card)  # calls normalize() / Gemini
```

**What this saves:** Eliminates Gemini calls for already-seen 9thgear listings. Directly fixes B2 (rate limit exhaustion).

**Schema change:** None. `sources` JSONB already has the URLs.

**New DB function needed:** `db.fetch_source_urls(source_name: str) -> set[str]`

---

## Implementation Steps

1. **`db.py`** — add two read functions:
   - `fetch_all_ids() -> set[str]` — `SELECT id FROM listings`
   - `fetch_source_urls(source: str) -> set[str]` — query `sources` JSONB for all URLs under a given source key

2. **`scrape.py`** — load `existing_ids` once before the SCRAPERS loop; filter `valid` listings through it before upserting

3. **`scrapers/nthgear.py`** — load `seen_urls` at start of `scrape()`; skip card if URL in set (before `normalize()` call)

4. **`scrapers/olx.py`** — same pattern as nthgear; OLX has fewer listings so lower priority but same fix

## Out of Scope

- Pagination early-stop (none of the scrapers paginate today)
- `last_scraped` timestamp table (adds complexity without clear payoff given the ID-set approach)
- Changing Cars24 sort from `bestmatch` to `newest`

## Files Touched

- `db.py`
- `scrape.py`
- `scrapers/nthgear.py`
- `scrapers/olx.py`
