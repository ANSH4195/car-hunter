"""
OLX scraper — Bangalore, Karnataka.
OLX is JS-heavy; we use crawl4ai to render and then parse the HTML.
Card structure (confirmed):
  Container: [data-aut-id="itemBox2"]
  Title:     [data-aut-id="itemTitle"]      → "Audi Q5"
  Price:     [data-aut-id="itemPrice"]      → "₹ 8,00,000"
  Subtitle:  [data-aut-id="itemSubTitle"]   → "2013 - 200,000 km"
  Link:      a[href]
  Image:     img[src]
"""
from __future__ import annotations
import asyncio
import re
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import parse_price, parse_kms

SOURCE = "olx"

QUERIES = [
    "used-Audi-diesel",
    "used-Volkswagen-Tiguan-diesel",
    "used-Skoda-Octavia-diesel",
    "used-Jeep-Compass-diesel",
]

CITY_SLUG = "bangalore_g4058984"

# Maps OLX title keywords → structured make/model
MAKE_MAP = {
    "audi": "Audi",
    "volkswagen": "Volkswagen", "vw": "Volkswagen",
    "skoda": "Skoda",
    "jeep": "Jeep",
}


def _search_url(query: str) -> str:
    return f"https://www.olx.in/{CITY_SLUG}/q-{query}"


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

        # Subtitle: "2013 - 200,000 km" or "2020 - 45000 km"
        year_m = re.search(r"\b(20\d{2})\b", subtitle)
        year   = int(year_m.group(1)) if year_m else 0

        km_m = re.search(r"([\d,]+)\s*km", subtitle, re.I)
        kms  = parse_kms(km_m.group(0)) if km_m else 0

        # Parse make from title
        title_lower = raw_title.lower()
        make = ""
        for kw, m in MAKE_MAP.items():
            if kw in title_lower:
                make = m
                break
        if not make:
            return None

        # Model is remaining words after make
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
            color="", location="Bangalore",
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
    results: list[CarListing] = []
    for query in QUERIES:
        url = _search_url(query)
        try:
            html = asyncio.run(_fetch_rendered(url))
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select('[data-aut-id="itemBox2"]')
            if not cards:
                print(f"[olx] no cards for: {query}")
                continue
            for card in cards:
                listing = _parse_card(card)
                if listing:
                    results.append(listing)
        except Exception as e:
            print(f"[olx] error for '{query}': {e}")
    return results
