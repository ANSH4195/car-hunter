"""
OLX scraper — Karnataka-wide, pre-filtered URL.
OLX is JS-heavy; we use crawl4ai to render and then parse the HTML.
Card structure (confirmed):
  Container: [data-aut-id="itemBox2"]
  Title:     [data-aut-id="itemTitle"]      → "Audi Q5"
  Price:     [data-aut-id="itemPrice"]      → "₹ 8,00,000"
  Subtitle:  [data-aut-id="itemSubTitle"]   → "2020 - 45,000 km"
  Link:      a[href]
  Image:     img[src]
"""
from __future__ import annotations
import asyncio
import datetime
import re
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import parse_price, parse_kms
from filters import MIN_YEAR, MAX_KMS, MAX_PRICE
import db

SOURCE = "olx"

STATE_CONFIGS = [
    {"slug": "karnataka_g2001159",      "state": "Karnataka"},
    {"slug": "madhya-pradesh_g2001162", "state": "Madhya Pradesh"},
]

# Maps OLX title keywords → structured make
MAKE_MAP = {
    "audi": "Audi",
    "bmw": "BMW",
    "mercedes-benz": "Mercedes-Benz", "mercedes": "Mercedes-Benz",
    "volkswagen": "Volkswagen", "vw": "Volkswagen",
    "skoda": "Skoda",
    "jeep": "Jeep",
    "ford": "Ford",
    "volvo": "Volvo",
}


def _listing_url(slug: str) -> str:
    current_year = datetime.date.today().year
    return (
        f"https://www.olx.in/en-in/{slug}/cars_c84"
        "?filter=make_eq_audi-1_and_bmw_and_ford_and_jeep_and_mercedes-benz_and_skoda_and_volkswagen_and_volvo"
        f"%2Cmileage_max_{MAX_KMS}"
        "%2Cmodel_eq_ford-endeavour_and_jeep-compass_and_skoda-kodiaq_and_skoda-octavia_and_volkswagen-tiguan"
        "%2Cpetrol_eq_diesel"
        f"%2Cprice_max_{MAX_PRICE}"
        f"%2Cyear_between_{MIN_YEAR - 1}_to_{current_year}"
    )


def _extract_url(card) -> str:
    link_el = card.select_one("a[href]")
    href = link_el["href"] if link_el else ""
    return href if href.startswith("http") else f"https://www.olx.in{href}"


def _parse_card(card) -> CarListing | None:
    try:
        title_el    = card.select_one('[data-aut-id="itemTitle"]')
        price_el    = card.select_one('[data-aut-id="itemPrice"]')
        subtitle_el = card.select_one('[data-aut-id="itemSubTitle"]')
        link_el     = card.select_one("a[href]")
        img_el      = card.select_one("img")

        if not title_el:
            return None

        raw_title = title_el.get_text(strip=True)
        raw_price = price_el.get_text(strip=True) if price_el else ""
        subtitle  = subtitle_el.get_text(strip=True) if subtitle_el else ""

        price = parse_price(raw_price) or 0

        # Subtitle: "2020 - 45,000 km"
        year_m = re.search(r"\b(20\d{2})\b", subtitle)
        year   = int(year_m.group(1)) if year_m else 0

        km_m = re.search(r"([\d,]+)\s*km", subtitle, re.I)
        kms  = parse_kms(km_m.group(0)) if km_m else 0

        title_lower = raw_title.lower()
        make = ""
        for kw, m in MAKE_MAP.items():
            if kw in title_lower:
                make = m
                break
        if not make:
            return None

        parts = raw_title.split()
        model   = parts[1] if len(parts) > 1 else ""
        variant = " ".join(parts[2:]) if len(parts) > 2 else ""

        href = link_el["href"] if link_el else ""
        url  = href if href.startswith("http") else f"https://www.olx.in{href}"

        image_url = ""
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-src") or ""

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel="Diesel", transmission="",
            color="", location="", state="",
            price=price, image_url=image_url,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[olx] card parse error: {e}")
        return None


async def _fetch_rendered(url: str) -> str:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    config = CrawlerRunConfig(page_timeout=30000)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.html or ""


def scrape() -> list[CarListing]:
    seen_urls = db.fetch_source_urls(SOURCE)
    results: list[CarListing] = []
    for cfg in STATE_CONFIGS:
        url = _listing_url(cfg["slug"])
        try:
            html = asyncio.run(_fetch_rendered(url))
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select('[data-aut-id="itemBox2"]')
            if not cards:
                print(f"[olx] no cards found for {cfg['state']}")
                continue
            for card in cards:
                if _extract_url(card) in seen_urls:
                    continue
                listing = _parse_card(card)
                if listing:
                    listing.state    = cfg["state"]
                    listing.location = cfg["state"]
                    results.append(listing)
        except Exception as e:
            print(f"[olx] error ({cfg['state']}): {e}")
    return results
