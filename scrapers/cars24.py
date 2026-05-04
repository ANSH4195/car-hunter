"""
Cars24 scraper — Bangalore, diesel, target makes.
Cars24 uses Next.js App Router (RSC); car data is client-side rendered.
We use crawl4ai to render, then parse card DOM.
Card structure (confirmed):
  Wrapper:     a[class*="carCardWrapper"][href]   → full listing URL
  Image:       img.shrinkOnTouch[src, alt]        → alt = "2018 Skoda Kodiaq - SUV - Diesel - Automatic - ₹18.33 lakh"
  KMs:         card text regex for "X,XX,XXX km"
  Variant:     card text, item between model name and km string
  Location:    last item in card text
Filter URL uses Cars24's f= syntax:
  make:=:audi   → exact make match (blanket — all models)
  ;model:in:m1  → restrict previous make to these models
"""
from __future__ import annotations
import asyncio
import datetime
import re
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import parse_price, parse_kms
from filters import MIN_YEAR, MAX_PRICE

SOURCE = "cars24"
BASE   = "https://www.cars24.com"

CITY_CONFIGS = [
    {"slug": "bangalore", "city_id": "4709", "state": "Karnataka"},
    {"slug": "bhopal",    "city_id": "2987", "state": "Madhya Pradesh"},
    {"slug": "indore",    "city_id": "2920", "state": "Madhya Pradesh"},
    {"slug": "gwalior",   "city_id": "2948", "state": "Madhya Pradesh"},
    {"slug": "jabalpur",  "city_id": "3119", "state": "Madhya Pradesh"},
]

MAKE_NORM = {
    "audi": "Audi", "bmw": "BMW",
    "mercedes": "Mercedes-Benz", "mercedes benz": "Mercedes-Benz", "mercedes-benz": "Mercedes-Benz",
    "volkswagen": "Volkswagen", "vw": "Volkswagen",
    "skoda": "Skoda", "jeep": "Jeep", "ford": "Ford", "volvo": "Volvo",
}


def _listing_url(city_slug: str, city_id: str) -> str:
    current_year = datetime.date.today().year
    make_f = (
        "make%3A%3D%3Aaudi"
        "%3AOR%3Amake%3A%3D%3Abmw"
        "%3AOR%3Amake%3A%3D%3Amercedes+benz"
        "%3AOR%3Amake%3A%3D%3Avolvo"
        "%3AOR%3Amake%3A%3D%3Ajeep%3Bmodel%3Ain%3Acompass"
        "%3AOR%3Amake%3A%3D%3Avolkswagen%3Bmodel%3Ain%3Atiguan"
        "%3AOR%3Amake%3A%3D%3Aford%3Bmodel%3Ain%3Aendeavour"
        "%3AOR%3Amake%3A%3D%3Askoda%3Bmodel%3Ain%3Akodiaq%2Coctavia"
    )
    return (
        f"{BASE}/buy-used-diesel-cars-{city_slug}/?"
        f"f=listingPrice%3Abw%3A50000%2C{MAX_PRICE}"
        f"&f={make_f}"
        f"&f=year%3Abw%3A{MIN_YEAR}%2C{current_year}"
        f"&f=odometer%3Abw%3A0%2C1000000"
        f"&sort=bestmatch&storeCityId={city_id}"
    )


def _parse_card(card) -> CarListing | None:
    try:
        # URL
        href = card.get("href", "")
        url  = href if href.startswith("http") else f"{BASE}{href}"

        # Image + rich alt text: "2018 Skoda Kodiaq - SUV - Diesel - Automatic - ₹18.33 lakh"
        img_el    = card.select_one("img.shrinkOnTouch") or card.select_one("img")
        img_src   = ""
        alt_text  = ""
        if img_el:
            img_src  = img_el.get("src") or ""
            alt_text = img_el.get("alt") or ""

        # Parse year, make, model from alt or card text
        card_text = card.get_text(separator=" | ", strip=True)

        # Year: first 4-digit number in card text
        year_m = re.search(r"\b(20\d{2})\b", card_text)
        year   = int(year_m.group(1)) if year_m else 0

        # Make + model: "2018 Skoda Kodiaq" → make="Skoda", model="Kodiaq"
        make_model_m = re.search(r"\b20\d{2}\s+(\w[\w-]*(?:\s+\w[\w-]*)?)\b", card_text)
        make  = ""
        model = ""
        if make_model_m:
            parts = make_model_m.group(1).split()
            make_raw = parts[0].lower()
            make  = MAKE_NORM.get(make_raw, parts[0].title())
            model = parts[1] if len(parts) > 1 else ""

        # Variant: from card text between model name and km line
        # e.g. "2018 Skoda Kodiaq | STYLE 2.0 TDI 4X4 AT | 1,14,645 km"
        variant = ""
        items = [p.strip() for p in card_text.split("|")]
        for i, item in enumerate(items):
            if re.search(r"\b20\d{2}\b", item) and i + 1 < len(items):
                candidate = items[i + 1].strip()
                if not re.search(r"km|diesel|auto|manual|petrol|₹|emi", candidate, re.I):
                    variant = candidate

        # KMs: "1,14,645 km" or "50,000 km"
        km_m = re.search(r"([\d,]+)\s*km", card_text, re.I)
        kms  = parse_kms(km_m.group(0)) if km_m else 0

        # Fuel + transmission from alt text or card text
        fuel  = "Diesel"
        trans = ""
        if "automatic" in (alt_text + card_text).lower() or " auto" in card_text.lower():
            trans = "Automatic"
        elif "manual" in (alt_text + card_text).lower():
            trans = "Manual"

        # Price: prefer "₹XX.XX lakh" (actual price, not EMI/MRP)
        price_m = re.search(r"₹\s*([\d.]+)\s*lakh", card_text, re.I)
        if price_m:
            price = int(float(price_m.group(1)) * 100_000)
        else:
            price_m2 = re.search(r"₹\s*([\d.]+)L\b", card_text)
            price = int(float(price_m2.group(1)) * 100_000) if price_m2 else 0

        # Location: last non-junk item in card text
        location = "Bangalore"
        for item in reversed(items):
            item = item.strip()
            if item and not re.search(r"₹|EMI|charges|stock|owned|wishlist|verified", item, re.I):
                if len(item) > 4:
                    location = item
                    break

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel=fuel, transmission=trans, color="",
            location=location, state="", price=price, image_url=img_src,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[cars24] card parse error: {e}")
        return None


async def _fetch_rendered(url: str) -> str:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    config = CrawlerRunConfig(page_timeout=40000, delay_before_return_html=5.0)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.html or ""


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    for cfg in CITY_CONFIGS:
        url = _listing_url(cfg["slug"], cfg["city_id"])
        try:
            html  = asyncio.run(_fetch_rendered(url))
            soup  = BeautifulSoup(html, "html.parser")
            cards = soup.select('[class*="carCardWrapper"]')
            if not cards:
                print(f"[cars24] no cards found for {cfg['slug']}")
                continue
            for card in cards:
                listing = _parse_card(card)
                if listing:
                    listing.state = cfg["state"]
                    results.append(listing)
        except Exception as e:
            print(f"[cars24] error ({cfg['slug']}): {e}")
    return results
