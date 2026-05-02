# OLX Scraper

## Approach
crawl4ai + Playwright rendering of a single pre-filtered URL.

## Why crawl4ai
OLX is a React SPA. The listing cards are client-rendered; static HTML fetched with httpx contains no `itemBox2` elements. Playwright renders the full page (30 s timeout) and hands off the populated DOM.

## The Filter URL
OLX's `/cars_c84` endpoint accepts a `filter=` query string with comma-separated predicates:

```
make_eq_audi-1_and_bmw_and_ford_and_jeep_and_mercedes-benz_and_skoda_and_volkswagen_and_volvo
mileage_max_150000
model_eq_ford-endeavour_and_jeep-compass_and_skoda-kodiaq_and_skoda-octavia_and_volkswagen-tiguan
petrol_eq_diesel
price_max_2500000
year_between_2016_to_<current_year>
```

**Key insight about make_eq + model_eq interaction**: makes that appear in `make_eq` but have *no* corresponding entry in `model_eq` return **all models** for that make (blanket). Makes that *do* have a `model_eq` entry are restricted to only those models. This lets one URL handle both "any Audi/BMW/Mercedes/Volvo" and "only Tiguan / only Compass / only Endeavour" simultaneously.

Previously the scraper ran 4 keyword search queries and returned 0 valid results. Switching to this pre-filtered URL immediately yielded ~18 on-target listings per run.

## Card Structure
```
[data-aut-id="itemBox2"]          ← container
  [data-aut-id="itemTitle"]       ← "Audi Q5" (make + model in title)
  [data-aut-id="itemPrice"]       ← "₹ 8,00,000"
  [data-aut-id="itemSubTitle"]    ← "2020 - 45,000 km"
  a[href]                         ← listing URL
  img[src]                        ← thumbnail
```

Year and km are parsed from subtitle with regex. Make is inferred from the title string via `MAKE_MAP`.

## Pagination
None — the single rendered page already loads all matching cards for the filters applied. OLX uses infinite-scroll but the initial render contains enough results for our narrow filter set.

## Known Limitations
- Transmission and color are not exposed on the listing card; both default to empty string.
- Location defaults to "Karnataka" (city-level data would require entering each listing).
