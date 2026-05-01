"""
CarWale scraper — Karnataka, Diesel, target makes.
URL format: /used/{city}/{make}/
Data is in window.__INITIAL_STATE__ → usedSearch.stocks (SSR JSON, ~28 results per page).
Diesel filter is applied in code since the URL doesn't support it.
"""
from __future__ import annotations
import json
import re
import httpx
from scrapers.base import CarListing

SOURCE = "carwale"
BASE   = "https://www.carwale.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.google.com/",
}

CITIES = ["bangalore", "mysore", "mangalore", "hubli"]
MAKES  = ["audi", "volkswagen", "skoda", "jeep", "ford"]


def _search_url(city: str, make: str) -> str:
    return f"{BASE}/used/{city}/{make}/"


def _extract_stocks(html: str) -> list[dict]:
    idx = html.find("window.__INITIAL_STATE__ = {")
    if idx < 0:
        return []
    start = idx + len("window.__INITIAL_STATE__ = ")
    depth = 0
    end_pos = start
    for i, c in enumerate(html[start:start + 800_000], start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end_pos = i + 1
                break
    try:
        data = json.loads(html[start:end_pos])
        return data.get("usedSearch", {}).get("stocks", [])
    except Exception as e:
        print(f"[carwale] __INITIAL_STATE__ parse error: {e}")
        return []


def _to_listing(stock: dict) -> CarListing | None:
    try:
        fuel = stock.get("fuel", "")
        if fuel.lower() != "diesel":
            return None

        make    = stock.get("makeName", "")
        model   = stock.get("rootName", "") or stock.get("modelName", "")
        variant = stock.get("versionName", "") or stock.get("trimName", "")
        year    = int(stock.get("makeYear") or 0)
        kms     = int(stock.get("kmNumeric") or 0)
        price   = int(stock.get("priceNumeric") or 0)
        trans   = stock.get("transmission", "")
        city    = stock.get("cityName", "") or stock.get("areaName", "")

        image_url = stock.get("imageUrl", "")
        if not image_url and stock.get("stockImages"):
            imgs = stock["stockImages"]
            if isinstance(imgs, list) and imgs:
                image_url = imgs[0].get("url", "")

        rel_url = stock.get("url", "")
        url = rel_url if rel_url.startswith("http") else f"{BASE}{rel_url}"

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel=fuel, transmission=trans, color="",
            location=city, price=price, image_url=image_url,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[carwale] stock parse error: {e}")
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
                        print(f"[carwale] {url} → {resp.status_code}")
                        continue
                    stocks = _extract_stocks(resp.text)
                    for stock in stocks:
                        listing = _to_listing(stock)
                        if listing:
                            results.append(listing)
                except Exception as e:
                    print(f"[carwale] error {url}: {e}")
    return results
