"""
OLX scraper — Bangalore, Karnataka.
OLX is JS-heavy; we use crawl4ai to render and then parse the HTML.
Falls back to a lightweight API probe.
"""
from __future__ import annotations
import asyncio
import re
import json
import httpx
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import normalize, parse_price, parse_kms

SOURCE = "olx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-IN",
}

QUERIES = ["used Audi diesel", "used Volkswagen Tiguan diesel",
           "used Skoda Octavia diesel", "used Jeep Compass diesel"]

# OLX Bangalore location ID
CITY_SLUG = "bangalore_g4058984"


def _search_url(query: str) -> str:
    q = query.replace(" ", "-")
    return f"https://www.olx.in/{CITY_SLUG}/q-{q}"


def _parse_html(html: str, query: str) -> list[CarListing]:
    soup = BeautifulSoup(html, "html.parser")
    listings: list[CarListing] = []

    # OLX listing cards use data-aut-id="itemBox" or li[data-aut-id]
    cards = soup.select('[data-aut-id="itemBox"]') or soup.select("li.EIR5N") or []

    for card in cards:
        try:
            title_el = card.select_one('[data-aut-id="itemTitle"]') or card.select_one("._2tW1I")
            price_el = card.select_one('[data-aut-id="itemPrice"]') or card.select_one("._89yzn")
            img_el   = card.select_one("img")
            link_el  = card.select_one("a")

            if not title_el:
                continue

            raw_text = title_el.get_text(" ", strip=True)
            raw_price = price_el.get_text(strip=True) if price_el else ""
            price = parse_price(raw_price) or 0

            image_url = ""
            if img_el:
                image_url = img_el.get("data-src") or img_el.get("src") or ""

            url = ""
            if link_el:
                href = link_el.get("href", "")
                url = href if href.startswith("http") else f"https://www.olx.in{href}"

            # Use Gemini to extract structured fields from the title text
            parsed = normalize(raw_text)
            if not parsed:
                continue

            listing = CarListing(
                make        = parsed.get("make") or "",
                model       = parsed.get("model") or "",
                variant     = parsed.get("variant") or "",
                year        = int(parsed.get("year") or 0),
                kms         = int(parsed.get("kms") or 0),
                fuel        = parsed.get("fuel") or "Diesel",
                transmission= parsed.get("transmission") or "",
                color       = parsed.get("color") or "",
                location    = parsed.get("location") or "Bangalore",
                price       = int(parsed.get("price_inr") or price or 0),
                image_url   = image_url,
                source_name = SOURCE,
                source_url  = url,
            )
            if listing.make and listing.model and listing.year:
                listings.append(listing)
        except Exception as e:
            print(f"[olx] card parse error: {e}")

    return listings


async def _fetch_rendered(url: str) -> str:
    from crawl4ai import AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return result.html or ""


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    for query in QUERIES:
        url = _search_url(query)
        try:
            # Try plain httpx first (faster)
            with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
                resp = client.get(url)
            html = resp.text

            # If page has no listings (JS-gated), use crawl4ai
            if 'data-aut-id="itemBox"' not in html and 'EIR5N' not in html:
                print(f"[olx] JS rendering needed for: {query}")
                html = asyncio.run(_fetch_rendered(url))

            listings = _parse_html(html, query)
            results.extend(listings)
        except Exception as e:
            print(f"[olx] error for '{query}': {e}")
    return results
