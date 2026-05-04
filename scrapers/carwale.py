"""
CarWale scraper — Karnataka, Diesel, target makes.
URL formats:
  broad: /used/{city}/{make}/          — any model, ~28 results/page
  model: /used/{city}/{make}-{model}/  — model-filtered, no server-side pagination beyond p1
Data is in window.__INITIAL_STATE__ → usedSearch.stocks (SSR JSON).
Diesel filter applied in code (no server-side fuel param exists).
"""
from __future__ import annotations
import json
import httpx
from scrapers.base import CarListing
from filters import CITY_STATE

SOURCE = "carwale"
BASE   = "https://www.carwale.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.google.com/",
}

CITIES = ["bangalore", "mysore", "mangalore", "hubli", "bhopal", "indore", "gwalior", "jabalpur"]

# Makes where any model is valid — use broad URL + paginate
ANY_MODEL = ["audi", "bmw", "mercedes-benz", "volvo"]

# Makes where only one model matters — use hyphenated make-model URL (server-side filtered)
# Note: /page-N/ pagination is broken on these URLs; page 1 covers all inventory for
# low-volume models (VW Tiguan, Skoda Octavia, Ford Endeavour). Jeep Compass has more
# stock but broad-URL page 1 also only returned ~22 Compass, so coverage is comparable.
MODEL_SPECIFIC: dict[str, str] = {
    "volkswagen": "tiguan",
    "skoda":      "octavia",
    "jeep":       "compass",
    "ford":       "endeavour",
}

PAGE_SIZE = 28  # stocks per page on broad URLs


def _broad_url(city: str, make: str, page: int = 1) -> str:
    if page == 1:
        return f"{BASE}/used/{city}/{make}/"
    return f"{BASE}/used/{city}/{make}/page-{page}/"


def _model_url(city: str, make: str, model: str) -> str:
    return f"{BASE}/used/{city}/{make}-{model}/"


def _extract_stocks_and_total(html: str) -> tuple[list[dict], int]:
    idx = html.find("window.__INITIAL_STATE__ = {")
    if idx < 0:
        return [], 0
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
        data  = json.loads(html[start:end_pos])
        us    = data.get("usedSearch", {})
        total = int(us.get("totalCount") or 0)
        return us.get("stocks", []), total
    except Exception as e:
        print(f"[carwale] __INITIAL_STATE__ parse error: {e}")
        return [], 0


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
        state   = CITY_STATE.get(city.lower(), "")

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
            location=city, state=state, price=price, image_url=image_url,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[carwale] stock parse error: {e}")
        return None


def _fetch_all_pages(client: httpx.Client, city: str, make: str) -> list[dict]:
    """Fetch all pages for a broad make URL."""
    all_stocks: list[dict] = []
    page = 1
    while True:
        url = _broad_url(city, make, page)
        try:
            resp = client.get(url)
            if resp.status_code != 200:
                print(f"[carwale] {url} → {resp.status_code}")
                break
            stocks, total = _extract_stocks_and_total(resp.text)
            if not stocks:
                break
            all_stocks.extend(stocks)
            if len(all_stocks) >= total or len(stocks) < PAGE_SIZE:
                break
            page += 1
        except Exception as e:
            print(f"[carwale] error {url}: {e}")
            break
    return all_stocks


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for city in CITIES:
            # Broad makes: paginate to get full inventory
            for make in ANY_MODEL:
                for stock in _fetch_all_pages(client, city, make):
                    listing = _to_listing(stock)
                    if listing:
                        results.append(listing)

            # Model-specific makes: single model URL (no server-side pagination on these)
            for make, model in MODEL_SPECIFIC.items():
                url = _model_url(city, make, model)
                try:
                    resp = client.get(url)
                    if resp.status_code != 200:
                        print(f"[carwale] {url} → {resp.status_code}")
                        continue
                    stocks, _ = _extract_stocks_and_total(resp.text)
                    for stock in stocks:
                        listing = _to_listing(stock)
                        if listing:
                            results.append(listing)
                except Exception as e:
                    print(f"[carwale] error {url}: {e}")
    return results
