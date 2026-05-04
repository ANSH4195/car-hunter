# O3 — Carwale URL filter: reduce 588 fetched listings

## Problem

`scrapers/carwale.py` hits 8 cities × 8 makes = **64 URLs**, each returning ~28 results
(one page of `window.__INITIAL_STATE__` JSON). Diesel is filtered in Python after fetch, not
at the URL level. Result: ~588 diesel listings fetched per run, most failing `is_valid()` on
make/model/year/kms grounds. That's wasted HTTP bandwidth and parse time.

Two levers to pull:

1. **Fuel-type query param** — does Carwale accept `?fueltype=diesel` (or equivalent) to
   pre-filter server-side?
2. **Model-level URL** — Carwale's URL structure supports `/used/{city}/{make}/{model}/`.
   Four of our eight targets are model-specific (Tiguan, Octavia, Compass, Endeavour). Using
   model-level URLs for those four would exclude all other models of that make from the
   response.

---

## Investigation steps

### Step 1 — Probe fuel-type query param

Carwale's search page is Next.js SSR; its URL for a diesel filter likely adds a query
parameter. Common candidates:

```
/used/bangalore/audi/?fueltype=diesel
/used/bangalore/audi/?fuel=diesel
/used/bangalore/audi/?FuelType=3          # numeric enum (diesel = 3 on some sites)
```

**Action**: Fetch one baseline URL (e.g. `/used/bangalore/audi/`) and one candidate fuel-
param URL with `httpx`. Compare:
- `len(stocks)` returned
- `set(s["fuel"] for s in stocks)` — does the filtered response contain only diesel?
- Does the URL redirect or return 200?

If a working param is found, add it to `_search_url()`.

### Step 2 — Probe model-level URL

Test whether `/used/bangalore/volkswagen/tiguan/` returns Tiguan-only stocks vs the broader
`/used/bangalore/volkswagen/` URL.

**Action**: Fetch both. If the model URL returns Tiguan stocks only and the response is valid
JSON (same `__INITIAL_STATE__` structure), we can split MAKES into two lists:

```python
# makes where any model is valid — keep broad URL
ANY_MODEL = ["audi", "bmw", "mercedes-benz", "volvo"]

# makes where only one model is valid — use model URL
MODEL_SPECIFIC = {
    "volkswagen": "tiguan",
    "skoda":      "octavia",
    "jeep":       "compass",
    "ford":       "endeavour",
}
```

`_search_url()` would emit `/used/{city}/{make}/` for ANY_MODEL and
`/used/{city}/{make}/{model}/` for MODEL_SPECIFIC entries.

### Step 3 — Check pagination necessity

Page 1 returns ~28 results. With the current broad URLs (all fuel types, all models) for
niche makes in mid-size Karnataka cities there are rarely >28 diesel results of that make in
stock. Verify: does `__INITIAL_STATE__` include a `totalCount` or `pageCount` field? If
post-filter counts never exceed 28, pagination is unnecessary and the current single-page
fetch is fine.

If a city+make combination does exceed 28 results after filtering, add pagination (append
`?page=N` or `/page-N/` depending on Carwale's URL scheme).

---

## Expected outcome

| Scenario | URLs/run | Est. listings fetched |
|----------|----------|-----------------------|
| Current | 64 | ~588 diesel |
| + fuel param only | 64 | ~588 diesel (same count, just fetched pre-filtered) |
| + model URLs for 4 makes | 32 any-model + 32 model-specific = 64 | fewer non-matching model results |
| Both combined | 64 | significantly reduced |

The biggest win is likely the **model-level URL** for VW/Skoda/Jeep/Ford — those four makes
have only one valid model each, so the broad make URL fetches many irrelevant models (e.g.
all VW Polo/Vento/T-Roc results when we only want Tiguan).

---

## Implementation changes (once probes confirm)

- `_search_url(city, make)` → `_search_url(city, make, model=None)` — appends `/{model}/`
  when provided, and appends `?fueltype=diesel` (or whatever param works)
- `MAKES` list split into `ANY_MODEL` list + `MODEL_SPECIFIC` dict
- Inner loop updated to call `_search_url` with model where applicable
- Diesel check in `_to_listing` kept as a safety net regardless

---

## Files to change

- `scrapers/carwale.py` — URL construction + loop logic
- No schema, filter, or DB changes needed
