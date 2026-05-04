"""
9thGear scraper — Bangalore luxury used cars.
Card text structure (pipe-delimited):
  BADGE | YEAR | MAKE MODEL VARIANT | REG_NO | FUEL | KMS km | PRICE | View Car
"""
from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import parse_price, parse_kms
from filters import CITY_STATE
import db

SOURCE = "9thgear"
BASE   = "https://www.9thgear.co.in"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# (title prefix tokens) → (canonical make, number of tokens to consume)
_MAKES = [
    (("MERCEDES", "BENZ"), "Mercedes-Benz", 2),
    (("VOLKSWAGEN",),      "Volkswagen",    1),
    (("VOLVO",),           "Volvo",         1),
    (("SKODA",),           "Skoda",         1),
    (("AUDI",),            "Audi",          1),
    (("BMW",),             "BMW",           1),
    (("JEEP",),            "Jeep",          1),
    (("FORD",),            "Ford",          1),
]


def _parse_title(title: str) -> tuple[str, str, str]:
    """'MERCEDES BENZ GLC 220D 4MATIC' → ('Mercedes-Benz', 'Glc', '220D 4Matic')"""
    words = title.upper().split()
    for prefixes, make, n in _MAKES:
        if tuple(words[:n]) == prefixes:
            rest    = words[n:]
            model   = rest[0].title() if rest else ""
            variant = " ".join(w.title() for w in rest[1:])
            return make, model, variant
    return "", "", ""


def _search_url(page: int = 1) -> str:
    return f"{BASE}/search?fuel=Diesel&page={page}"


def _extract_url(card) -> str:
    link_el = card.select_one("a[href*='luxury-used-cars']") or card.select_one("a")
    href = link_el["href"] if link_el else ""
    return href if href.startswith("http") else f"{BASE}{href}"


def _parse_card(card) -> CarListing | None:
    try:
        parts = [p.strip() for p in card.get_text(" | ", strip=True).split(" | ")]
        # BADGE | YEAR | TITLE | REG | FUEL | KMS | PRICE | View Car
        if len(parts) < 7:
            return None

        year  = int(parts[1]) if parts[1].isdigit() else 0
        title = parts[2]
        kms   = parse_kms(parts[5]) or 0
        price = parse_price(parts[6]) or 0
        fuel  = parts[4].strip() or "Diesel"

        make, model, variant = _parse_title(title)
        if not make or not model:
            return None

        link_el   = card.select_one("a[href*='luxury-used-cars']") or card.select_one("a")
        href      = link_el["href"] if link_el else ""
        url       = href if href.startswith("http") else f"{BASE}{href}"

        img_el    = card.select_one("img[src*='upload']") or card.select_one("img")
        image_url = ""
        if img_el:
            src = img_el.get("src") or img_el.get("data-src") or ""
            image_url = src if src.startswith("http") else f"{BASE}{src}"

        loc   = "Bangalore"
        state = CITY_STATE.get(loc.lower(), "Karnataka")
        return CarListing(
            make=make, model=model, variant=variant,
            year=year, kms=kms, fuel=fuel, transmission="",
            color="", location=loc, state=state,
            price=price, image_url=image_url,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[9thgear] card parse error: {e}")
        return None


def scrape() -> list[CarListing]:
    seen_urls = db.fetch_source_urls(SOURCE)
    results: list[CarListing] = []
    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for page in range(1, 5):
            url = _search_url(page)
            try:
                resp = client.get(url)
                if resp.status_code != 200:
                    break
                soup  = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select(".main-car")
                if not cards:
                    break
                for card in cards:
                    if _extract_url(card) in seen_urls:
                        continue
                    listing = _parse_card(card)
                    if listing:
                        results.append(listing)
            except Exception as e:
                print(f"[9thgear] error page {page}: {e}")
                break
    return results
