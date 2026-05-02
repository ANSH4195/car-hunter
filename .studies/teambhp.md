# TeamBHP Scraper

## Approach
Plain httpx with spoofed browser headers + BeautifulSoup. The classifieds site is **server-rendered PHP** — no JavaScript execution needed.

## Why httpx (not crawl4ai)
TeamBHP's classifieds (`classifieds.team-bhp.com`) returns fully-populated HTML on the first GET. The listing rows including all card content are in the static response. crawl4ai would add unnecessary overhead.

## Model IDs
TeamBHP's search form uses internal numeric make/model IDs rather than human-readable slugs. The IDs live in a `tree_MakeModel` JavaScript object embedded in the page HTML. They were extracted manually (2026-05-01) and hardcoded as `MODEL_IDS`:

- Audi: 11 mainstream model IDs
- BMW: 10 mainstream model IDs
- Mercedes-Benz: 13 mainstream model IDs
- Volvo: 8 model IDs (all)
- VW Tiguan, Skoda Octavia, Jeep Compass, Ford Endeavour: 1 ID each

The search URL encodes these as repeated `MakeModel[in][N]=ID` params with a sequential index.

## Search URL
```
/search_results/?action=search
  &listing_type[equal]=Car
  &MakeModel[in][1]=2983&MakeModel[in][2]=2013...   ← all model IDs
  &multyModelMode=1
  &CarFuelType[equal]=Diesel
  &page=1
```

## PHP Session Pagination
TeamBHP search is stateful: the server stores the search parameters in a PHP session keyed by session cookie.

- **Page 1**: full URL with all `MakeModel[in]` params — this registers the search in the server session and returns page 1 results
- **Pages 2+**: `?restore=1&page=N` — the server replays the stored search for the same session cookie

httpx's `Client` persists cookies across requests within the same session, so the `restore=1` approach works automatically. Without session persistence, pages 2+ return the same 20 rows as page 1 (the server falls back to a default search).

## Card Structure
```
tr                                 ← one listing per table row
  .sr_info                         ← pipe-delimited text block:
                                     "2014 Audi Q3 | Location: | Chennai | Km: | 120000 | Fuel type: | Diesel | ..."
  .sr_price                        ← "Rs.1,280,000"
  img[src]                         ← thumbnail
  a[href*="/buy-used-for-sale/N"]  ← listing URL (contains unique numeric ID)
```

All fields are parsed from `.sr_info` text by splitting on `|` and using a label-lookup helper (`_after("Km:")`).

## Deduplication
Within a single scrape run, listings are deduplicated by `source_url` (the `/buy-used-for-sale/N` URL). This guards against duplicate rows if the same listing appears across pages.

## Known Limitations
- The `restore=1` mechanism depends on the PHP session cookie surviving across the full pagination loop. If the server session expires mid-run, pages 2+ may revert to the default search.
- TeamBHP's classifieds inventory is small (~50 listings for these makes/fuel nationally); 9 pages is a generous cap.
