"""
CarWale scraper — Karnataka, Diesel, target makes.
CarWale serves partial SSR HTML; listings are in <script> JSON-LD or inline JSON.
"""
from __future__ import annotations
import json
import re
import httpx
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import parse_price, parse_kms

SOURCE  = "carwale"
MAKES   = ["Audi", "Volkswagen", "Skoda", "Jeep"]
BASE    = "https://www.carwale.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.google.com/",
}


def _search_url(make: str, page: int = 1) -> str:
    return (
        f"{BASE}/used/cars-in-karnataka/"
        f"?filters=FuelTypes.Diesel_Makes.{make}"
        f"&page={page}"
    )


def _parse_listing_card(card) -> CarListing | None:
    try:
        title_el = card.select_one("h2") or card.select_one(".title") or card.select_one("[class*='title']")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        price_el = card.select_one("[class*='price']") or card.select_one("strong")
        raw_price = price_el.get_text(strip=True) if price_el else ""
        price = parse_price(raw_price) or 0

        # Metadata: "82,000 km | Diesel | Bangalore"
        meta_el = card.select_one("[class*='spec']") or card.select_one("[class*='detail']")
        meta = meta_el.get_text(" ", strip=True) if meta_el else ""

        kms = 0
        location = "Karnataka"
        fuel = "Diesel"
        trans = ""
        km_m = re.search(r"([\d,]+)\s*km", meta, re.IGNORECASE)
        if km_m:
            kms = parse_kms(km_m.group(0)) or 0
        loc_parts = [p.strip() for p in meta.split("|")]
        if len(loc_parts) >= 3:
            location = loc_parts[-1]
        if "Automatic" in meta:
            trans = "Automatic"
        elif "Manual" in meta:
            trans = "Manual"

        link_el = card.select_one("a[href]")
        href    = link_el["href"] if link_el else ""
        url     = href if href.startswith("http") else f"{BASE}{href}"

        img_el    = card.select_one("img")
        image_url = ""
        if img_el:
            image_url = img_el.get("data-src") or img_el.get("src") or ""

        # Parse title: "Used Audi Q5 Premium Plus 2021"
        title_clean = re.sub(r"^[Uu]sed\s+", "", title)
        parts = title_clean.split()
        make    = parts[0] if parts else ""
        model   = parts[1] if len(parts) > 1 else ""
        variant = " ".join(parts[2:-1]) if len(parts) > 3 else ""
        year    = int(parts[-1]) if parts and parts[-1].isdigit() and len(parts[-1]) == 4 else 0

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel=fuel, transmission=trans, color="",
            location=location, price=price, image_url=image_url,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[carwale] card parse error: {e}")
        return None


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for make in MAKES:
            for page in range(1, 4):   # up to 3 pages per make
                url = _search_url(make, page)
                try:
                    resp = client.get(url)
                    if resp.status_code != 200:
                        print(f"[carwale] {url} → {resp.status_code}")
                        break
                    soup  = BeautifulSoup(resp.text, "html.parser")
                    cards = (
                        soup.select("[class*='listing']")
                        or soup.select("[class*='card']")
                        or soup.select("article")
                    )
                    if not cards:
                        break
                    for card in cards:
                        listing = _parse_listing_card(card)
                        if listing:
                            results.append(listing)
                except Exception as e:
                    print(f"[carwale] error {url}: {e}")
                    break
    return results
