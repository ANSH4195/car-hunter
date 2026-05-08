"""
TeamBHP Classifieds scraper — nationwide diesel listings.
The site is server-rendered; plain httpx works (no crawl4ai needed).
Card structure (confirmed):
  Row:     tr > td containing .sr_info
  Title:   a[href*='/buy-used-for-sale/'] with text "YEAR MAKE MODEL"
  Info:    .sr_info text → "YEAR Make Model | Location: | X | Km: | N | Fuel type: | ..."
  Price:   .sr_price → "Rs.1,280,000"
  Image:   img[src] in the same tr
  Pagination: &page=N
MakeModel IDs sourced from tree_MakeModel JS object on classifieds.team-bhp.com.
"""
from __future__ import annotations
import re
import httpx
from bs4 import BeautifulSoup
from scrapers.base import CarListing
from normalizer import parse_kms
from filters import CITY_STATE

SOURCE = "teambhp"
BASE   = "https://classifieds.team-bhp.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8",
    "Referer": "https://www.google.com/",
}

# Model IDs from tree_MakeModel in TeamBHP's page JS (extracted 2026-05-01)
MODEL_IDS = [
    # Audi — all mainstream models
    2983, 2013, 3151, 349,  3141, 2630, 3244, 2703, 2168, 1977, 3322,
    # BMW — mainstream
    2877, 1652, 1653, 2673, 1654, 2071, 2160, 1657, 2616, 3216,
    # Mercedes-Benz — mainstream
    2569, 2467, 1669, 2875, 2912, 1736, 2298, 2818, 3086, 3108, 1738, 1737, 2595,
    # Volvo — all
    2486, 2097, 3232, 3010, 3195, 3270, 2869, 2747,
    # VW Tiguan, Skoda Octavia, Jeep Compass, Ford Endeavour, Mitsubishi Pajero Sport
    3037, 1613, 3042, 1991, 2812,
]

MAKE_NORM = {
    "audi": "Audi", "bmw": "BMW",
    "mercedes": "Mercedes-Benz", "mercedes-benz": "Mercedes-Benz",
    "volkswagen": "Volkswagen", "vw": "Volkswagen",
    "skoda": "Skoda", "jeep": "Jeep", "ford": "Ford", "volvo": "Volvo",
    "mitsubishi": "Mitsubishi",
}


def _search_url(page: int = 1) -> str:
    # Build MakeModel[in][N]=ID params with sequential index
    mm_params = "&".join(
        f"MakeModel%5Bin%5D%5B{i+1}%5D={mid}"
        for i, mid in enumerate(MODEL_IDS)
    )
    return (
        f"{BASE}/search_results/?action=search"
        f"&listing_type%5Bequal%5D=Car"
        f"&{mm_params}"
        f"&multyModelMode=1"
        f"&CarFuelType%5Bequal%5D=Diesel"
        f"&adv_button="
        f"&page={page}"
    )


def _parse_row(row) -> CarListing | None:
    try:
        info_el  = row.find(class_="sr_info")
        price_el = row.find(class_="sr_price")
        img_el   = row.find("img")
        link_el  = row.find("a", href=re.compile(r"/buy-used-for-sale/\d+"))

        if not info_el:
            return None

        # Parse info text: "2014 Audi Q3 | Location: | Chennai, TN | Km: | 120000 | Fuel type: | Diesel | Transmission: | Automatic | Variant: | Q3 3.5TDI | Posted on: | ..."
        parts = [p.strip() for p in info_el.get_text(separator="|").split("|")]
        parts = [p for p in parts if p]  # drop empties

        def _after(label: str) -> str:
            for i, p in enumerate(parts):
                if label.lower() in p.lower() and i + 1 < len(parts):
                    return parts[i + 1].strip()
            return ""

        title   = parts[0] if parts else ""  # "2014 Audi Q3"
        title_p = title.split()
        year    = int(title_p[0]) if title_p and title_p[0].isdigit() else 0
        make_raw = title_p[1].lower() if len(title_p) > 1 else ""
        make     = MAKE_NORM.get(make_raw, make_raw.title())
        model    = " ".join(title_p[2:]) if len(title_p) > 2 else ""

        location    = _after("Location:")
        kms_raw     = _after("Km:")
        fuel        = _after("Fuel type:")
        trans_raw   = _after("Transmission:")
        variant     = _after("Variant:")

        kms   = parse_kms(kms_raw) or 0
        trans = ""
        if "automatic" in trans_raw.lower():
            trans = "Automatic"
        elif "manual" in trans_raw.lower():
            trans = "Manual"

        # Price: "Rs.1,280,000" → INR int
        price = 0
        if price_el:
            price_text = price_el.get_text(strip=True).replace(",", "").replace("Rs.", "").strip()
            price = int(price_text) if price_text.isdigit() else 0

        href = link_el["href"] if link_el else ""
        url  = href if href.startswith("http") else f"{BASE}{href}"

        img_src = img_el.get("src", "") if img_el else ""

        if not all([make, model, year, price]):
            return None

        state = CITY_STATE.get(location.lower().split(",")[0].strip(), "")
        return CarListing(
            make=make, model=model, variant=variant, year=year,
            kms=kms, fuel=fuel or "Diesel", transmission=trans, color="",
            location=location, state=state, price=price, image_url=img_src,
            source_name=SOURCE, source_url=url,
        )
    except Exception as e:
        print(f"[teambhp] card parse error: {e}")
        return None


async def _fetch_crawl4ai(url: str) -> str:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    config = CrawlerRunConfig(page_timeout=30000)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.html or ""


def _scrape_page_html(html: str) -> list[CarListing]:
    soup = BeautifulSoup(html, "html.parser")
    return [r for r in soup.find_all("tr") if r.find(class_="sr_info")]


def scrape() -> list[CarListing]:
    import asyncio
    results: list[CarListing] = []
    seen_urls: set[str] = set()
    use_crawl4ai = False

    with httpx.Client(headers=HEADERS, timeout=25, follow_redirects=True) as client:
        for page in range(1, 10):
            url = _search_url(page) if (page == 1 or use_crawl4ai) else f"{BASE}/search_results/?restore=1&page={page}"
            try:
                if use_crawl4ai:
                    html = asyncio.run(_fetch_crawl4ai(url))
                else:
                    resp = client.get(url)
                    if resp.status_code == 403:
                        print(f"[teambhp] page {page} → 403, retrying with crawl4ai")
                        use_crawl4ai = True
                        html = asyncio.run(_fetch_crawl4ai(_search_url(page)))
                    elif resp.status_code != 200:
                        print(f"[teambhp] page {page} → {resp.status_code}")
                        break
                    else:
                        html = resp.text

                rows = _scrape_page_html(html)
                if not rows:
                    break
                new_this_page = 0
                for row in rows:
                    listing = _parse_row(row)
                    if listing and listing.source_url not in seen_urls:
                        seen_urls.add(listing.source_url)
                        results.append(listing)
                        new_this_page += 1
                if new_this_page == 0:
                    break
            except Exception as e:
                print(f"[teambhp] error page {page}: {e}")
                break
    return results
