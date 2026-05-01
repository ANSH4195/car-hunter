"""
Cars24 scraper — Karnataka, Diesel, target makes.
Data lives in __NEXT_DATA__ JSON embedded in the page HTML.
"""
from __future__ import annotations
import json
import re
import httpx
from scrapers.base import CarListing

SOURCE = "cars24"
MAKES  = ["Audi", "Volkswagen", "Skoda", "Jeep", "Ford"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

# Karnataka city slugs on Cars24
CITIES = ["bangalore", "mysore", "mangalore", "hubli"]


def _search_url(city: str, make: str) -> str:
    return f"https://www.cars24.com/buy-used-{make.lower()}-cars-{city}/?f=fuel%3ADiesel&sort=bestmatch"


def _parse_next_data(html: str) -> list[dict]:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
        # Path: props.pageProps.carList or searchResult.cars
        page = data.get("props", {}).get("pageProps", {})
        cars = (
            page.get("carList")
            or page.get("searchResult", {}).get("content")
            or []
        )
        return cars if isinstance(cars, list) else []
    except Exception as e:
        print(f"[cars24] JSON parse error: {e}")
        return []


def _to_listing(raw: dict, city: str) -> CarListing | None:
    try:
        car_id  = raw.get("id") or raw.get("carId", "")
        make    = raw.get("make", "")
        model   = raw.get("model", "")
        variant = raw.get("variant") or raw.get("variantDisplayName", "")
        year    = int(raw.get("makeYear") or raw.get("year") or 0)
        kms     = int(raw.get("km") or raw.get("kilometer") or raw.get("odometerReading") or 0)
        price   = int(raw.get("price") or raw.get("carPrice") or 0)
        fuel    = raw.get("fuelType", "")
        trans   = raw.get("transmission", "")
        color   = raw.get("color") or raw.get("carColor") or ""
        location = raw.get("city") or city.title()

        # Image: prefer first item in images array
        images = raw.get("images") or raw.get("carImages") or []
        image_url = images[0] if isinstance(images, list) and images else ""
        if isinstance(image_url, dict):
            image_url = image_url.get("url") or image_url.get("imageUrl") or ""

        url = f"https://www.cars24.com/buy-used-{make.lower()}-{model.lower()}-cars/{car_id}/"

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel=fuel, transmission=trans, color=color,
            location=location, price=price, image_url=image_url,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[cars24] listing parse error: {e}")
        return None


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for city in CITIES:
            for make in MAKES:
                url = _search_url(city, make)
                try:
                    resp = client.get(url)
                    if resp.status_code != 200:
                        print(f"[cars24] {url} → {resp.status_code}")
                        continue
                    raw_cars = _parse_next_data(resp.text)
                    for raw in raw_cars:
                        listing = _to_listing(raw, city)
                        if listing:
                            results.append(listing)
                except Exception as e:
                    print(f"[cars24] error fetching {url}: {e}")
    return results
