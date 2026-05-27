"""
OLX scraper — state-wide, pre-filtered URL.
OLX pages are CSR shells; car data lives in a window.__APP JSON blob in a <script> tag.
We extract ordered item IDs from the collections dict and parse each item's parameters.
"""
from __future__ import annotations
import asyncio
import datetime
import re
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from filters import MIN_YEAR, MAX_KMS, MAX_PRICE
import db

SOURCE = "olx"

STATE_CONFIGS = [
    {"slug": "karnataka_g2001159",      "state": "Karnataka"},
    {"slug": "madhya-pradesh_g2001162", "state": "Madhya Pradesh"},
]


def _listing_url(slug: str) -> str:
    current_year = datetime.date.today().year
    return (
        f"https://www.olx.in/en-in/{slug}/cars_c84"
        "?filter=make_eq_audi-1_and_bmw_and_ford_and_jeep_and_mercedes-benz_and_skoda_and_volkswagen_and_volvo"
        f"%2Cmileage_max_{MAX_KMS}"
        "%2Cmodel_eq_ford-endeavour_and_jeep-compass_and_skoda-kodiaq_and_volkswagen-tiguan"
        "%2Cpetrol_eq_diesel"
        f"%2Cprice_max_{MAX_PRICE}"
        f"%2Cyear_between_{MIN_YEAR - 1}_to_{current_year}"
    )


def _get_app_script(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", string=re.compile(r"window\.__APP"))
    return tag.string if tag else None


def _parse_item(raw: str, item_id: str, state: str) -> CarListing | None:
    try:
        pos = raw.find(f'"{item_id}":{{"id":"{item_id}"')
        if pos == -1:
            return None
        block = raw[pos: pos + 12000]

        title_m = re.search(r'"title":"([^"]+)"', block)
        price_m = re.search(r'"raw":(\d+)', block)
        make_m  = re.search(r'"key":"make","value_name":"([^"]+)"', block)
        model_m = re.search(r'"key":"model","value_name":"([^"]+)"', block)
        year_m  = re.search(r'"key":"year","value_name":"(\d{4})"', block)
        km_m    = re.search(r'"key":"mileage","value_name":"([\d,]+)"', block)
        fuel_m  = re.search(r'"key":"petrol","value_name":"([^"]+)"', block)
        trans_m = re.search(r'"key":"transmission","value_name":"([^"]+)"', block)
        city_m  = re.search(r'"ADMIN_LEVEL_3_name":"([^"]+)"', block)
        img_m   = re.search(r'"url":"(https(?:\\u002F|/)[^"]+(?:\\u002F|/)image)"', block)

        if not (title_m and price_m and make_m and year_m):
            return None

        make  = make_m.group(1).strip()
        model = model_m.group(1).strip() if model_m else ""
        year  = int(year_m.group(1))
        price = int(price_m.group(1))
        kms   = int(km_m.group(1).replace(",", "")) if km_m else 0
        fuel  = fuel_m.group(1).strip() if fuel_m else "Diesel"
        trans = trans_m.group(1).strip() if trans_m else ""
        city  = city_m.group(1).strip() if city_m else state

        img_raw   = img_m.group(1) if img_m else ""
        image_url = img_raw.replace("\\u002F", "/")

        return CarListing(
            make=make, model=model, variant="", year=year,
            kms=kms, fuel=fuel, transmission=trans,
            color="", location=city, state=state,
            price=price, image_url=image_url,
            source_name=SOURCE, source_url=f"https://www.olx.in/en-in/item/iid-{item_id}",
        )
    except Exception as e:
        print(f"[olx] item {item_id} parse error: {e}")
        return None


async def _scrape_async(seen_urls: set) -> list[CarListing]:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    config = CrawlerRunConfig(page_timeout=30000)
    results: list[CarListing] = []
    async with AsyncWebCrawler() as crawler:
        for cfg in STATE_CONFIGS:
            base_url = _listing_url(cfg["slug"])
            page = 1
            while True:
                url = f"{base_url}&page={page}"
                try:
                    result = await crawler.arun(url=url, config=config)
                    raw = _get_app_script(result.html or "")
                    if not raw:
                        print(f"[olx] no window.__APP on page {page} for {cfg['state']}, stopping")
                        break

                    # Pick the largest collection of item IDs on the page
                    coll_matches = re.findall(r'"items#[^"]+":\[([^\]]*)\]', raw)
                    all_id_lists = [re.findall(r'"(\d+)"', m) for m in coll_matches]
                    item_ids = max(all_id_lists, key=len) if all_id_lists else []

                    if not item_ids:
                        print(f"[olx] no items on page {page} for {cfg['state']}, stopping")
                        break

                    print(f"[olx] {cfg['state']} page {page}: {len(item_ids)} items")
                    for item_id in item_ids:
                        if f"https://www.olx.in/en-in/item/iid-{item_id}" in seen_urls:
                            continue
                        listing = _parse_item(raw, item_id, cfg["state"])
                        if listing:
                            results.append(listing)

                    if len(item_ids) < 40:
                        break
                    page += 1
                except Exception as e:
                    print(f"[olx] error ({cfg['state']} page {page}): {e}")
                    break
    return results


def scrape() -> list[CarListing]:
    seen_urls = db.fetch_source_urls(SOURCE)
    return asyncio.run(_scrape_async(seen_urls))
