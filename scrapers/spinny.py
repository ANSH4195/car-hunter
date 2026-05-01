"""
Spinny scraper — Bengaluru, Diesel, target makes.
Spinny is Next.js; data is in __NEXT_DATA__.
Also tries their internal API endpoint.
"""
from __future__ import annotations
import json
import re
import httpx
from scrapers.base import CarListing
from normalizer import parse_price, parse_kms

SOURCE = "spinny"
MAKES  = ["audi", "bmw", "mercedes-benz", "volkswagen", "skoda", "jeep", "ford", "volvo"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/html",
}


def _search_url(make: str) -> str:
    return f"https://www.spinny.com/used-cars/bengaluru/{make}/?fuel=Diesel"


def _api_url(make: str, page: int = 1) -> str:
    # Spinny internal search API (discovered via network inspection)
    return (
        f"https://www.spinny.com/api/v4/cars/search/?"
        f"city=bengaluru&make={make}&fuel_type=diesel&page={page}&page_size=30"
    )


def _parse_next_data(html: str) -> list[dict]:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return []
    try:
        data  = json.loads(m.group(1))
        page  = data.get("props", {}).get("pageProps", {})
        cars  = page.get("cars") or page.get("listings") or page.get("results") or []
        return cars if isinstance(cars, list) else []
    except Exception as e:
        print(f"[spinny] JSON parse error: {e}")
        return []


def _to_listing(raw: dict) -> CarListing | None:
    try:
        make     = raw.get("make", "")
        model    = raw.get("model", "")
        variant  = raw.get("variant") or raw.get("subvariant", "")
        year     = int(raw.get("year") or raw.get("make_year") or 0)
        kms      = int(raw.get("kms_driven") or raw.get("kms") or raw.get("odometer", 0))
        price    = int(raw.get("price") or raw.get("selling_price") or 0)
        fuel     = raw.get("fuel_type") or raw.get("fuel", "")
        trans    = raw.get("transmission", "")
        color    = raw.get("color") or raw.get("colour", "")
        location = raw.get("city") or raw.get("location", "Bengaluru")

        images   = raw.get("images") or raw.get("car_images") or []
        img      = images[0] if images else {}
        image_url = img.get("url") or img.get("image_url") or (img if isinstance(img, str) else "")

        slug     = raw.get("slug") or raw.get("id") or ""
        url      = f"https://www.spinny.com/used-cars/bengaluru/{slug}/" if slug else "https://www.spinny.com"

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel=fuel, transmission=trans, color=color,
            location=location, price=price, image_url=image_url,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[spinny] listing parse error: {e}")
        return None


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for make in MAKES:
            # Try API first
            try:
                resp = client.get(_api_url(make))
                if resp.status_code == 200:
                    data = resp.json()
                    raw_cars = data.get("results") or data.get("cars") or data.get("data") or []
                    for raw in raw_cars:
                        listing = _to_listing(raw)
                        if listing:
                            results.append(listing)
                    continue
            except Exception:
                pass

            # Fall back to __NEXT_DATA__ HTML parse
            try:
                resp = client.get(_search_url(make))
                if resp.status_code == 200:
                    for raw in _parse_next_data(resp.text):
                        listing = _to_listing(raw)
                        if listing:
                            results.append(listing)
            except Exception as e:
                print(f"[spinny] error for {make}: {e}")
    return results
