"""
Spinny scraper — direct REST API (no Playwright/crawl4ai needed).
API: https://api.spinny.com/v3/api/listing/v6/
- Luxury brands (Audi, BMW, Mercedes-Benz, Volvo, Jeep): car_category=luxury
- Non-luxury targets (VW Tiguan, Skoda Octavia, Ford Endeavour, Mitsubishi): make= + model= params
Response fields: id, make, model, variant, make_year, price, mileage, fuel_type,
  transmission, color, city, permanent_url, images[0].file.absurl
"""
from __future__ import annotations
import time
import httpx
from scrapers.base import CarListing

SOURCE = "spinny"
BASE   = "https://www.spinny.com"
API    = "https://api.spinny.com/v3/api/listing/v6/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin": "https://www.spinny.com",
    "Referer": "https://www.spinny.com/",
    "Accept": "application/json",
}

CITY_CONFIGS = [
    {"slug": "bangalore", "state": "Karnataka"},
    {"slug": "bhopal",    "state": "Madhya Pradesh"},
    {"slug": "indore",    "state": "Madhya Pradesh"},
]

# Non-luxury targets; luxury brands (Audi/BMW/Mercedes/Volvo) use car_category=luxury
NON_LUXURY_TARGETS = [
    {"make": "volkswagen", "model": "tiguan"},
    {"make": "skoda",      "model": "octavia"},
    {"make": "ford",       "model": "endeavour"},
    {"make": "mitsubishi", "model": "pajero-sport"},
]

MAKE_NORM = {
    "audi": "Audi", "bmw": "BMW",
    "mercedes-benz": "Mercedes-Benz", "mercedes benz": "Mercedes-Benz",
    "volkswagen": "Volkswagen", "skoda": "Skoda", "jeep": "Jeep",
    "ford": "Ford", "volvo": "Volvo", "mitsubishi": "Mitsubishi",
}


def _parse_listing(item: dict, state: str) -> CarListing | None:
    try:
        make_raw = (item.get("make") or "").lower().strip()
        make     = MAKE_NORM.get(make_raw, make_raw.title())
        model    = (item.get("model") or "").strip()
        variant  = (item.get("variant") or "").strip()
        year     = int(item.get("make_year") or 0)
        price    = int(float(item.get("price") or 0))
        kms      = int(item.get("mileage") or 0)
        fuel     = (item.get("fuel_type") or "diesel").strip()
        trans    = (item.get("transmission") or "").strip().title()
        color    = (item.get("color") or "").strip().title()
        city     = (item.get("city") or "").strip()

        perm_url = item.get("permanent_url") or ""
        url = f"{BASE}{perm_url}" if perm_url.startswith("/") else perm_url

        images  = item.get("images") or []
        img_src = ""
        if images and isinstance(images[0], dict):
            file_obj = images[0].get("file") or {}
            raw = file_obj.get("absurl") or ""
            img_src = ("https:" + raw) if raw.startswith("//") else raw

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel=fuel, transmission=trans, color=color,
            location=city or "Bangalore", state=state, price=price,
            image_url=img_src, source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[spinny] parse error: {e}")
        return None


def _fetch_pages(client: httpx.Client, params: dict, state: str) -> list[CarListing]:
    results: list[CarListing] = []
    seen_urls: set[str] = set()
    for page in range(1, 6):
        try:
            resp = client.get(API, params={**params, "page": page, "page_size": 20})
            if resp.status_code != 200:
                print(f"[spinny] HTTP {resp.status_code} — {params}")
                break
            data  = resp.json()
            items = data.get("results") or []
            if not items:
                break
            new_this_page = 0
            for item in items:
                listing = _parse_listing(item, state)
                if listing and listing.source_url not in seen_urls:
                    seen_urls.add(listing.source_url)
                    results.append(listing)
                    new_this_page += 1
            if new_this_page == 0 or not data.get("next"):
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"[spinny] error (page {page}, {params}): {e}")
            break
    return results


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    seen_urls: set[str] = set()

    with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        for cfg in CITY_CONFIGS:
            for listing in _fetch_pages(
                client,
                {"city": cfg["slug"], "car_category": "luxury", "fuel_type": "diesel"},
                cfg["state"],
            ):
                if listing.source_url not in seen_urls:
                    seen_urls.add(listing.source_url)
                    results.append(listing)
            time.sleep(0.3)

            for target in NON_LUXURY_TARGETS:
                for listing in _fetch_pages(
                    client,
                    {"city": cfg["slug"], "fuel_type": "diesel", **target},
                    cfg["state"],
                ):
                    if listing.source_url not in seen_urls:
                        seen_urls.add(listing.source_url)
                        results.append(listing)
                time.sleep(0.3)

    return results
