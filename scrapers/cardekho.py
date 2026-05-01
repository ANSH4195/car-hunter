"""
CarDekho scraper — Karnataka, Diesel, target makes.
Card structure confirmed:
  Container: div.NewUcExCard
  Title: div.titlebox h3  → "YEAR Make Model Variant" (year may be prepended)
  Specs: text near titlebox  → "X kms • Fuel • Transmission"
  Price: element with class containing 'price'
  Link: a[href] → /used-car-details/...
"""
from __future__ import annotations
import re
import httpx
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import parse_price, parse_kms

SOURCE  = "cardekho"
MAKES   = ["Audi", "Volkswagen", "Skoda", "Jeep", "Ford"]
BASE    = "https://www.cardekho.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-IN",
    "Referer": "https://www.google.com/",
}


def _search_url(make: str, page: int = 1) -> str:
    return f"{BASE}/used-cars/used-{make}-cars-in-karnataka?fuel=Diesel&page={page}"


def _parse_card(card) -> CarListing | None:
    try:
        title_el = card.select_one(".titlebox h3") or card.select_one("h3") or card.select_one("h2")
        if not title_el:
            return None
        title = title_el.get_text(" ", strip=True)

        year_m = re.search(r"\b(20\d{2})\b", title)
        year   = int(year_m.group(1)) if year_m else 0
        title_no_year = re.sub(r"\b20\d{2}\b", "", title).strip()
        parts  = title_no_year.split()
        make   = parts[0] if parts else ""
        model  = parts[1] if len(parts) > 1 else ""
        variant = " ".join(parts[2:]) if len(parts) > 2 else ""

        price_el  = card.select_one("[class*='price']") or card.select_one(".price")
        raw_price = price_el.get_text(strip=True) if price_el else ""
        price     = parse_price(raw_price) or 0

        # Specs text: "X kms • Fuel • Transmission"
        card_text = card.get_text(" ", strip=True)
        km_m = re.search(r"([\d,]+)\s*kms?", card_text, re.IGNORECASE)
        kms  = parse_kms(km_m.group(0)) if km_m else 0

        trans = "Automatic" if "Automatic" in card_text else ("Manual" if "Manual" in card_text else "")

        location_el = card.select_one("[class*='location']") or card.select_one("[class*='city']")
        location    = location_el.get_text(strip=True) if location_el else "Karnataka"

        link_el = card.select_one("a[href*='used-car-details']") or card.select_one("a[href]")
        href    = link_el["href"] if link_el else ""
        url     = href if href.startswith("http") else f"{BASE}{href}"

        img_el    = card.select_one("img")
        image_url = ""
        if img_el:
            image_url = img_el.get("data-src") or img_el.get("src") or ""

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms or 0, fuel="Diesel", transmission=trans, color="",
            location=location, price=price, image_url=image_url,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[cardekho] card parse error: {e}")
        return None


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for make in MAKES:
            for page in range(1, 4):
                url = _search_url(make, page)
                try:
                    resp = client.get(url)
                    if resp.status_code != 200:
                        print(f"[cardekho] {url} → {resp.status_code}")
                        break
                    soup  = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select(".NewUcExCard")
                    if not cards:
                        break
                    for card in cards:
                        listing = _parse_card(card)
                        if listing:
                            results.append(listing)
                except Exception as e:
                    print(f"[cardekho] error {url}: {e}")
                    break
    return results
