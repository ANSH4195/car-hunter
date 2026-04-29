"""
9thGear scraper — Bangalore luxury used cars.
Card structure confirmed:
  Container: div.main-car (inside div.col-lg-3.col-md-3.col-sm-6)
  Title: h3 > a (ALL CAPS — converted with .title())
  Price: span/text containing ₹
  KMs: text containing km
  Link: a[href] containing 'luxury-used-cars'
"""
from __future__ import annotations
import re
import httpx
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import parse_price, parse_kms, normalize

SOURCE = "9thgear"
BASE   = "https://www.9thgear.co.in"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

TARGET_MAKES = {"audi", "volkswagen", "vw", "skoda", "jeep"}


def _search_url(page: int = 1) -> str:
    return f"{BASE}/search?fuel=Diesel&page={page}"


def _parse_card(card) -> CarListing | None:
    try:
        title_el = card.select_one("h3") or card.select_one("h2")
        if not title_el:
            return None
        title = title_el.get_text(strip=True).title()  # 9thGear is ALL CAPS

        if not any(m in title.lower() for m in TARGET_MAKES):
            return None

        link_el   = card.select_one("a[href*='luxury-used-cars']") or card.select_one("a")
        href      = link_el["href"] if link_el else ""
        url       = href if href.startswith("http") else f"{BASE}{href}"

        img_el    = card.select_one("img[src*='upload']") or card.select_one("img")
        image_url = ""
        if img_el:
            src = img_el.get("src") or img_el.get("data-src") or ""
            image_url = src if src.startswith("http") else f"{BASE}{src}"

        price_el  = card.select_one("span.posted_by")
        price     = parse_price(price_el.get_text(strip=True)) if price_el else 0

        km_el = card.find(string=re.compile(r"\d+\s*km", re.I))
        kms   = parse_kms(str(km_el)) if km_el else 0

        year_m = re.search(r"\b(20\d{2})\b", card.get_text())
        year   = int(year_m.group(1)) if year_m else 0

        parsed = normalize(title)
        if not parsed:
            return None

        make    = parsed.get("make") or ""
        model   = parsed.get("model") or ""
        variant = parsed.get("variant") or ""
        if not parsed.get("year"):
            parsed["year"] = year
        if not parsed.get("kms"):
            parsed["kms"] = kms
        if not parsed.get("price_inr"):
            parsed["price_inr"] = price

        return CarListing(
            make        = make,
            model       = model,
            variant     = variant,
            year        = int(parsed.get("year") or year or 0),
            kms         = int(parsed.get("kms") or kms or 0),
            fuel        = parsed.get("fuel") or "Diesel",
            transmission= parsed.get("transmission") or "",
            color       = parsed.get("color") or "",
            location    = "Bangalore",
            price       = int(parsed.get("price_inr") or price or 0),
            image_url   = image_url,
            source_name = SOURCE,
            source_url  = url,
        )
    except Exception as e:
        print(f"[9thgear] card parse error: {e}")
        return None


def scrape() -> list[CarListing]:
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
                    listing = _parse_card(card)
                    if listing:
                        results.append(listing)
            except Exception as e:
                print(f"[9thgear] error page {page}: {e}")
                break
    return results
