# Scraper API Reverse Engineering: Cars24 & Spinny

**Date:** 2026-05-08  
**Bug:** B3a — Cars24 and Spinny returning 0 results on GitHub Actions  
**Commit:** `3cbae83`

---

## What broke

Cars24 and Spinny scrapers worked locally but returned 0 listings on every scheduled and manual GitHub Actions run from at least 2026-05-03.

Both scrapers were using **crawl4ai + Playwright** (a headless Chromium browser) to render the pages before parsing the HTML. Locally the CSS selectors found cards; on Actions they found nothing.

---

## Why it broke

GitHub Actions runners use Microsoft Azure datacenter IPs. Both Cars24 and Spinny detect these IPs and respond differently to browser traffic from them:

- **Cars24** returned a page with the correct shell HTML but an empty listing section — the React components rendered with no data cards.
- **Spinny** returned the page HTML but the React app never populated the listing grid.

This is a common anti-scraping measure: the site fingerprints the request (IP range, TLS fingerprint, browser behaviour patterns) and serves a degraded response that passes a basic HTTP check but contains no real data. The `simulate_user=True, magic=True` flags in crawl4ai 0.4.247 had no effect because the block is applied before any JS execution, at the IP layer.

The root cause was using a **browser-rendered approach for sites that were actually serving usable data at the HTTP layer** — we just hadn't found the right endpoint.

---

## How it was fixed

### Cars24 — Next.js RSC endpoint

Cars24 runs on **Next.js App Router with React Server Components (RSC)**. In this architecture, the server pre-renders page data and sends it as a wire-format stream of JSON chunks rather than as a traditional HTML page.

When a browser navigates to a listing page, Next.js also issues a secondary fetch with an `RSC: 1` request header to get the server-rendered component tree. This secondary fetch returns the **full listing data as embedded JSON** in the response body — no JavaScript execution required.

**Request:**
```
GET https://www.cars24.com/buy-used-diesel-cars-bangalore/?f=...&storeCityId=4709
Headers:
  RSC: 1
  Accept: text/x-component,*/*
  User-Agent: Mozilla/5.0 (Chrome)
```

**Response:** ~1 MB of RSC wire format containing a JSON blob like:
```json
{"content": [{"appointmentId": "...", "make": "Audi", "model": "Q5", "year": 2021, "listingPrice": 2850000, "odometer": {"value": 62000}, ...}], "totalCars": 24, "searchAfter": "...cursor..."}
```

**Parsing strategy:** `json.JSONDecoder.raw_decode()` is pointed at the `"content":[` substring in the response text. It parses the full JSON array without needing to understand the surrounding RSC wire format. The `searchAfter` cursor found just after the array's closing `]` is used to fetch subsequent pages.

**Key fields extracted:**

| API field | CarListing field |
|---|---|
| `appointmentId` | dedup key (via `cdpRelativeUrl`) |
| `make`, `model`, `variant` | make, model, variant |
| `year` | year |
| `listingPrice` | price (INR integer) |
| `odometer.value` | kms |
| `transmissionType.value` | transmission |
| `fuelType` | fuel |
| `color` | color |
| `listingImage.uri` | image_url |
| `cdpRelativeUrl` | source_url (prepend `https://www.cars24.com/`) |
| `address.locality` | location |

This approach completely removes the Playwright dependency for Cars24 and is not affected by Azure IP blocks because there is no browser fingerprint — it is an ordinary HTTPS GET.

---

### Spinny — Internal REST API

Spinny is a React + Redux SPA. Its listing pages are entirely client-rendered: the SSR HTML contains an empty `cars: []` array in the Redux initial state, and the browser fetches listing data separately via RxJS epics after page load.

The API domain is **`api.spinny.com`**, which is distinct from `www.spinny.com` and does not appear to have the same IP-based bot protection on the listing endpoint.

**Endpoint:** `https://api.spinny.com/v3/api/listing/v6/`

**Query parameters:**

| Param | Value |
|---|---|
| `city` | `bangalore`, `bhopal`, `indore` |
| `fuel_type` | `diesel` |
| `car_category` | `luxury` (for Audi/BMW/Mercedes/Volvo/Jeep) |
| `make` + `model` | for non-luxury targets (VW/Skoda/Ford/Mitsubishi) |
| `page` | 1–N |
| `page_size` | 20 |

**Why two query strategies:** Spinny's `make=` filter does not work correctly for luxury brands — they are segmented into a separate `car_category=luxury` pool. A single `?car_category=luxury&fuel_type=diesel` query returns all Audi, BMW, Mercedes-Benz, Volvo, and Jeep Compass listings together. Non-luxury targets (Volkswagen Tiguan, Skoda Octavia, Ford Endeavour, Mitsubishi Pajero Sport) require individual `make=volkswagen&model=tiguan` style queries. `filters.py` `is_valid()` handles final filtering in both cases.

**Key response fields:**

| API field | CarListing field |
|---|---|
| `make`, `model`, `variant` | make, model, variant |
| `make_year` | year |
| `price` | price (float INR, cast to int) |
| `mileage` | kms |
| `fuel_type` | fuel |
| `transmission` | transmission |
| `color` | color |
| `city` | location |
| `permanent_url` | source_url (prepend `https://www.spinny.com`) |
| `images[0].file.absurl` | image_url (prepend `https:` if `//`-relative) |

Pagination: loop until `results` is empty or the `next` field is null.

---

## What remains broken (B3b)

**TeamBHP** (`classifieds.team-bhp.com`) is server-rendered and returns **HTTP 403** on Azure IPs before any content is served. The crawl4ai fallback also receives 403 because the block is at the network/IP layer — no amount of browser emulation or header spoofing helps.

Options to fix TeamBHP:
- **Self-hosted GitHub Actions runner** on a home machine or non-cloud VPS (`runs-on: self-hosted` in `scrape.yml`, zero code changes)
- **Residential proxy** passed to httpx (`proxies=` argument)

TeamBHP listings from earlier runs remain in the DB and continue to display in the dashboard.
