"""
TeamBHP Classifieds scraper.
The site returned 403 in direct tests; we spoof a browser session with
a full header set including Referer. Falls back to crawl4ai if still blocked.
"""
from __future__ import annotations
import asyncio
import re
import httpx
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import normalize, parse_price, parse_kms

SOURCE = "teambhp"
BASE   = "https://classifieds.team-bhp.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "navigate",
}

MAKES   = ["Audi", "Volkswagen", "Skoda", "Jeep"]

# TeamBHP classifieds search — state=29 is Karnataka, cat=Cars
def _search_url(make: str, page: int = 1) -> str:
    return f"{BASE}/?cat=Cars&make={make}&fuel=Diesel&state=29&page={page}"


async def _crawl4ai_fetch(url: str) -> str:
    from crawl4ai import AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.html or ""


def _parse_html(html: str) -> list[CarListing]:
    soup = BeautifulSoup(html, "html.parser")
    listings: list[CarListing] = []

    # TeamBHP classifieds uses a table or div-based grid
    cards = (
        soup.select(".classified-listing")
        or soup.select("[class*='listing']")
        or soup.select(".car-item")
        or soup.select("article")
        or soup.select("td.listing-cell")
    )

    for card in cards:
        try:
            title_el  = card.select_one("h2, h3, .title, [class*='title']")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            link_el = card.select_one("a[href]")
            href    = link_el["href"] if link_el else ""
            url     = href if href.startswith("http") else f"{BASE}{href}"

            price_el  = card.select_one("[class*='price'], .price")
            raw_price = price_el.get_text(strip=True) if price_el else ""
            price     = parse_price(raw_price) or 0

            km_m = re.search(r"([\d,]+)\s*km", card.get_text(), re.I)
            kms  = parse_kms(km_m.group(0)) if km_m else 0

            img_el    = card.select_one("img")
            image_url = ""
            if img_el:
                image_url = img_el.get("data-src") or img_el.get("src") or ""
                if image_url and not image_url.startswith("http"):
                    image_url = f"{BASE}{image_url}"

            parsed = normalize(title)
            if not parsed:
                continue

            listing = CarListing(
                make        = parsed.get("make") or "",
                model       = parsed.get("model") or "",
                variant     = parsed.get("variant") or "",
                year        = int(parsed.get("year") or 0),
                kms         = int(parsed.get("kms") or kms or 0),
                fuel        = parsed.get("fuel") or "Diesel",
                transmission= parsed.get("transmission") or "",
                color       = parsed.get("color") or "",
                location    = parsed.get("location") or "Karnataka",
                price       = int(parsed.get("price_inr") or price or 0),
                image_url   = image_url,
                source_name = SOURCE,
                source_url  = url,
            )
            if listing.make and listing.model and listing.year:
                listings.append(listing)
        except Exception as e:
            print(f"[teambhp] card parse error: {e}")
    return listings


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    for make in MAKES:
        for page in range(1, 4):
            url = _search_url(make, page)
            try:
                with httpx.Client(headers=HEADERS, timeout=25, follow_redirects=True) as client:
                    resp = client.get(url)

                if resp.status_code == 403:
                    print(f"[teambhp] 403 on {url}, trying crawl4ai")
                    html = asyncio.run(_crawl4ai_fetch(url))
                elif resp.status_code != 200:
                    print(f"[teambhp] {url} → {resp.status_code}")
                    break
                else:
                    html = resp.text

                batch = _parse_html(html)
                if not batch:
                    break
                results.extend(batch)
            except Exception as e:
                print(f"[teambhp] error {url}: {e}")
                break
    return results
