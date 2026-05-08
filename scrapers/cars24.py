"""
Cars24 scraper — RSC (React Server Components) payload parsing.
Cars24 uses Next.js App Router; fetching with `RSC: 1` header returns the
full listing data as JSON embedded in the RSC wire format — no Playwright needed.
Listing JSON fields: appointmentId, make, model, variant, year, listingPrice,
  odometer.value, transmissionType.value, fuelType, color, listingImage.uri,
  cdpRelativeUrl, address.locality, searchAfter (pagination cursor).
"""
from __future__ import annotations
import datetime
import json
import re
import time
import httpx
from scrapers.base import CarListing
from filters import MIN_YEAR, MAX_PRICE

SOURCE = "cars24"
BASE   = "https://www.cars24.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/x-component,*/*",
    "RSC": "1",
    "Referer": "https://www.cars24.com/",
}

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
    "mitsubishi": "Mitsubishi",
}


def _listing_url(city_slug: str, city_id: str, search_after: str = "") -> str:
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
        "%3AOR%3Amake%3A%3D%3Amitsubishi%3Bmodel%3Ain%3Apajero+sport"
    )
    url = (
        f"{BASE}/buy-used-diesel-cars-{city_slug}/?"
        f"f=listingPrice%3Abw%3A50000%2C{MAX_PRICE}"
        f"&f={make_f}"
        f"&f=year%3Abw%3A{MIN_YEAR}%2C{current_year}"
        f"&f=odometer%3Abw%3A0%2C110000"
        f"&sort=bestmatch&storeCityId={city_id}"
    )
    if search_after:
        from urllib.parse import quote
        url += f"&searchAfter={quote(search_after)}"
    return url


def _extract_content(text: str) -> tuple[list[dict], str]:
    """Find the listings array in the RSC wire-format payload."""
    decoder = json.JSONDecoder()
    search_from = 0
    while True:
        idx = text.find('"content":[', search_from)
        if idx == -1:
            break
        arr_start = idx + len('"content":')
        try:
            arr, arr_end = decoder.raw_decode(text, arr_start)
        except (json.JSONDecodeError, ValueError):
            search_from = idx + 1
            continue
        if not isinstance(arr, list) or not arr:
            search_from = idx + 1
            continue
        if isinstance(arr[0], dict) and "appointmentId" in arr[0]:
            cursor_m = re.search(r'"searchAfter":"([^"]+)"', text[arr_end:arr_end + 300])
            cursor = cursor_m.group(1) if cursor_m else ""
            return arr, cursor
        search_from = idx + 1
    return [], ""


def _parse_listing(item: dict, state: str) -> CarListing | None:
    try:
        make_raw = (item.get("make") or "").lower().strip()
        make     = MAKE_NORM.get(make_raw, make_raw.title())
        model    = (item.get("model") or "").strip()
        variant  = (item.get("variant") or "").strip()
        year     = int(item.get("year") or 0)
        price    = int(item.get("listingPrice") or 0)

        odo = item.get("odometer") or {}
        kms = int(odo.get("value") or 0) if isinstance(odo, dict) else 0

        fuel      = (item.get("fuelType") or "Diesel").strip()
        trans_obj = item.get("transmissionType") or {}
        trans     = (trans_obj.get("value") or "").strip() if isinstance(trans_obj, dict) else ""
        color     = (item.get("color") or "").strip().title()

        img_obj = item.get("listingImage") or {}
        img_src = (img_obj.get("uri") or "") if isinstance(img_obj, dict) else ""

        rel_url = item.get("cdpRelativeUrl") or ""
        url     = f"{BASE}/{rel_url.lstrip('/')}" if rel_url else ""

        addr     = item.get("address") or {}
        location = (addr.get("locality") or addr.get("city") or "Bangalore").strip()

        if not all([make, model, year, price]):
            return None

        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel=fuel, transmission=trans, color=color,
            location=location, state=state, price=price,
            image_url=img_src, source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[cars24] parse error: {e}")
        return None


def scrape() -> list[CarListing]:
    results: list[CarListing] = []
    seen_urls: set[str] = set()

    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for cfg in CITY_CONFIGS:
            search_after = ""
            for page_num in range(1, 6):
                url = _listing_url(cfg["slug"], cfg["city_id"], search_after)
                try:
                    resp = client.get(url)
                    if resp.status_code != 200:
                        print(f"[cars24] {cfg['slug']} page {page_num}: HTTP {resp.status_code}")
                        break
                    items, next_cursor = _extract_content(resp.text)
                    if not items:
                        print(f"[cars24] {cfg['slug']} page {page_num}: no listings in RSC payload")
                        break
                    new_this_page = 0
                    for item in items:
                        listing = _parse_listing(item, cfg["state"])
                        if listing and listing.source_url and listing.source_url not in seen_urls:
                            seen_urls.add(listing.source_url)
                            results.append(listing)
                            new_this_page += 1
                    if not next_cursor or new_this_page == 0:
                        break
                    search_after = next_cursor
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[cars24] error ({cfg['slug']} page {page_num}): {e}")
                    break

    return results
