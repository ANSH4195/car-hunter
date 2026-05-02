# Cars24 Scraper

## Approach
crawl4ai + Playwright rendering of a pre-filtered search URL using Cars24's `f=` filter syntax.

## Why crawl4ai
Cars24 migrated to **Next.js App Router with React Server Components (RSC)**. The SSR shell that httpx fetches contains an empty `carList` — all car data is injected client-side after hydration. The old approach of extracting `__NEXT_DATA__` stopped working because RSC splits the payload differently (no monolithic JSON block). crawl4ai + Playwright renders the full React tree including the hydrated cards.

## The Filter URL
Cars24 uses a `f=` query parameter with URL-encoded filter expressions:

```
listingPrice:bw:50000,<MAX_PRICE>
make:=:audi:OR:make:=:bmw:OR:make:=:mercedes benz:OR:make:=:volvo
:OR:make:=:jeep;model:in:compass
:OR:make:=:volkswagen;model:in:tiguan
:OR:make:=:ford;model:in:endeavour
:OR:make:=:skoda;model:in:kodiaq,octavia
year:bw:<MIN_YEAR>,<current_year>
odometer:bw:0,1000000
```

Blanket makes (`audi`, `bmw`, `mercedes benz`, `volvo`) use `make:=:` without a `model:in:` clause. Model-restricted makes chain `;model:in:` directly after `make:=:`. The whole expression is URL-encoded (`%3A` = `:`, `%3B` = `;`, `%2C` = `,`).

## Card Structure
```
a[class*="carCardWrapper"][href]          ← container + listing URL
  img.shrinkOnTouch[src, alt]             ← alt = "2018 Skoda Kodiaq - SUV - Diesel - Automatic - ₹18.33 lakh"
  (card text)                             ← "2018 Skoda Kodiaq | STYLE 2.0 TDI | 1,14,645 km | Bangalore"
```

The image `alt` text is the most structured field: it contains year, make, model, body type, fuel, transmission and price in a known format. Year/make/model are parsed from card text with regex. Price is extracted as `₹XX.XX lakh` → integer INR. Variant is the pipe-separated item between the model name and the km string.

## Pagination
Not implemented — a single crawl4ai render returns all cards loaded on first paint. Cards24's `sort=bestmatch` ordering means the most relevant results appear first. For the narrow filter set (~5–20 listings) a single page is sufficient.

## Known Limitations
- Color is not exposed on cards.
- crawl4ai requires a 5 s `delay_before_return_html` to let React hydration finish before the DOM is captured.
