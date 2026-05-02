# Spinny Scraper

## Approach
crawl4ai + Playwright rendering of a pre-filtered search URL with a JSON `filterObject` query parameter.

## Why crawl4ai
Spinny is a client-side React app. All listing cards are rendered in the browser after JavaScript executes; plain httpx returns an empty shell with no car data.

## The Filter URL
Spinny accepts filters as a JSON object URL-encoded into a `filterObject` query parameter:

```python
filter_obj = {
    "fuel_type": ["diesel"],
    "make": ["audi", "bmw", "jeep", "mercedes-benz", "volvo"],  # blanket makes
    "max_mileage": ["150000"],
    "max_price": 2500000,
    "min_year": "2017",
    "model": ["endeavour", "octavia", "tiguan", "tiguan-allspace"],  # restricted models
}
url = f"/used-cars-in-bangalore/s/?filterObject={quote(json.dumps(filter_obj))}"
```

Blanket makes (Audi, BMW, Jeep, Mercedes-Benz, Volvo) go in `"make"`. Model-restricted makes (VW, Skoda, Ford) only have their specific model slugs in `"model"` — Spinny treats unmatched `model` entries as additional filters on top of `make`, effectively doing "make=jeep OR (model=tiguan OR model=octavia OR model=endeavour)".

## Card Structure
```
.CarListingCardV2__carListingCardV2Root    ← container
  span.ListingBrandModelDetail__make       ← "2017 Mercedes CLA" (year + make + model)
  .ListingPricingDetail__variant           ← "200 CDI Sport"
  [data-price]                             ← "1899920" (INR integer as attribute)
  a.ListingBrandModelDetail__makeModelLink ← listing URL
  img.ListingCarImage__productImage        ← thumbnail (src or data-src)
  .CarListingCardDetail__otherDetails      ← location string
```

The `data-price` attribute gives a clean integer INR value, avoiding price-text parsing entirely. KMs are extracted from card text with a regex matching `Xk km` or `X,XX,XXX km` patterns.

## Pagination
Up to 4 pages, each fetched with a separate crawl4ai call. The page number is appended as `"page": ["N"]` inside `filterObject`. The loop stops early when a page returns no cards (signals end of results).

## Known Limitations
- Color is not exposed on listing cards.
- crawl4ai requires a 4 s render delay for Spinny's React hydration to complete.
- Spinny's inventory for these makes in Bangalore is small (typically 5–15 listings); all fit on page 1.
