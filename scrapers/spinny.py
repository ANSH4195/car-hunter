"""
Spinny scraper — Bengaluru diesel listings via crawl4ai.
Spinny is a client-side React app; we render with Playwright via crawl4ai.
Card structure (confirmed):
  Container: .CarListingCardV2__carListingCardV2Root
  Make/Year: span.ListingBrandModelDetail__make  → "2017 Mercedes CLA"
  Variant:   .ListingPricingDetail__variant       → "200 CDI Sport"
  Price:     [data-price]                         → "1899920" (INR)
  Link:      a.ListingBrandModelDetail__makeModelLink[href]
  Image:     img.ListingCarImage__productImage[src or data-src]
  KMs/trans: parsed from card text (e.g. "50.5K km ... automatic")
  Location:  .CarListingCardDetail__otherDetails
"""
from __future__ import annotations
import asyncio
import json
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import parse_kms
from filters import MIN_YEAR, MAX_KMS, MAX_PRICE

SOURCE = "spinny"
BASE   = "https://www.spinny.com"

# Spinny city slugs (verify MP cities at spinny.com — not all cities are served).
CITY_CONFIGS = [
    {"slug": "bangalore", "state": "Karnataka"},
    {"slug": "bhopal",    "state": "Madhya Pradesh"},
    {"slug": "indore",    "state": "Madhya Pradesh"},
]

MAKE_NORM = {
    "audi": "Audi",
    "bmw": "BMW",
    "mercedes": "Mercedes-Benz",
    "mercedes-benz": "Mercedes-Benz",
    "volkswagen": "Volkswagen",
    "vw": "Volkswagen",
    "skoda": "Skoda",
    "jeep": "Jeep",
    "ford": "Ford",
    "volvo": "Volvo",
}


def _listing_url(city_slug: str, page: int = 1) -> str:
    filter_obj: dict = {
        "fuel_type": ["diesel"],
        "make": ["audi", "bmw", "jeep", "mercedes-benz", "volvo"],
        "max_mileage": [str(MAX_KMS)],
        "max_price": [MAX_PRICE],
        "min_year": [str(MIN_YEAR)],
        "model": ["endeavour", "octavia", "tiguan", "tiguan-allspace"],
    }
    if page > 1:
        filter_obj["page"] = [str(page)]
    return f"{BASE}/used-cars-in-{city_slug}/s/?filterObject={quote(json.dumps(filter_obj))}"


def _parse_card(card) -> CarListing | None:
    try:
        link_el    = card.select_one("a.ListingBrandModelDetail__makeModelLink")
        make_el    = card.select_one("span.ListingBrandModelDetail__make")
        variant_el = card.select_one(".ListingPricingDetail__variant")
        price_el   = card.select_one("[data-price]")
        img_el     = card.select_one("img.ListingCarImage__productImage")
        other_el   = card.select_one(".CarListingCardDetail__otherDetails")

        if not make_el:
            return None

        # "2017 Mercedes CLA" → year=2017, make="Mercedes-Benz", model="CLA"
        parts    = make_el.get_text(strip=True).split()
        year     = int(parts[0]) if parts and parts[0].isdigit() else 0
        make_raw = parts[1].lower() if len(parts) > 1 else ""
        make     = MAKE_NORM.get(make_raw, make_raw.title())
        model    = parts[2] if len(parts) > 2 else ""

        variant = variant_el.get_text(strip=True) if variant_el else ""
        price   = int(price_el.get("data-price") or 0) if price_el else 0

        href = link_el["href"] if link_el else ""
        url  = href if href.startswith("http") else f"{BASE}{href}"

        img_src = ""
        if img_el:
            img_src = img_el.get("src") or img_el.get("data-src") or ""
            if img_src and img_src.startswith("//"):
                img_src = "https:" + img_src

        location = other_el.get_text(strip=True) if other_el else "Bangalore"

        card_text = card.get_text(separator=" ", strip=True)
        km_m = re.search(r"([\d,.]+\s*[Kk]?\s*km)", card_text)
        kms  = parse_kms(km_m.group(1)) if km_m else 0

        trans = ""
        if "automatic" in card_text.lower():
            trans = "Automatic"
        elif "manual" in card_text.lower():
            trans = "Manual"

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel="Diesel", transmission=trans, color="",
            location=location, state="", price=price, image_url=img_src,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[spinny] card parse error: {e}")
        return None


async def _fetch_rendered(url: str) -> str:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    config = CrawlerRunConfig(page_timeout=40000, delay_before_return_html=4.0)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.html or ""


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    seen_urls: set[str] = set()
    for cfg in CITY_CONFIGS:
        for page in range(1, 5):
            url = _listing_url(cfg["slug"], page)
            try:
                html  = asyncio.run(_fetch_rendered(url))
                soup  = BeautifulSoup(html, "html.parser")
                cards = soup.select(".CarListingCardV2__carListingCardV2Root")
                if not cards:
                    print(f"[spinny] no cards for {cfg['slug']} page {page}, stopping")
                    break
                new_this_page = 0
                for card in cards:
                    listing = _parse_card(card)
                    if listing and listing.source_url not in seen_urls:
                        seen_urls.add(listing.source_url)
                        listing.state = cfg["state"]
                        results.append(listing)
                        new_this_page += 1
                if new_this_page == 0:
                    break
            except Exception as e:
                print(f"[spinny] error {cfg['slug']} page {page}: {e}")
                break
    return results
