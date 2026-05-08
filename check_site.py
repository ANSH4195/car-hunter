"""
Playwright inspector: access the Streamlit app frame directly.
"""
import asyncio
from playwright.async_api import async_playwright

URL = "https://car-hunter.streamlit.app"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        print(f"Loading {URL} ...")
        await page.goto(URL, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # The actual app lives in the /~/+/ iframe — navigate directly to it
        app_page = await browser.new_page(viewport={"width": 1280, "height": 900})
        print("Navigating to app iframe URL directly...")
        await app_page.goto(f"{URL}/~/+/", timeout=60000, wait_until="domcontentloaded")

        # Wait for Streamlit to boot and render listings
        print("Waiting up to 60s for listings to render...")
        try:
            await app_page.wait_for_selector(".car-card", timeout=60000)
            print("Car cards appeared!")
        except Exception:
            print("car-card timeout — checking what's on screen")

        await app_page.wait_for_timeout(3000)
        await app_page.screenshot(path="/tmp/car_hunter_app.png", full_page=False)
        print("Screenshot: /tmp/car_hunter_app.png")

        # ── counts ────────────────────────────────────────────────────────
        cards = await app_page.query_selector_all(".car-card")
        print(f"\nCar cards: {len(cards)}")

        thumbs = await app_page.query_selector_all("img.car-thumb")
        broken, ok = [], []
        for img in thumbs:
            src = await img.get_attribute("src") or ""
            nat_w = await img.evaluate("el => el.naturalWidth")
            (broken if nat_w == 0 else ok).append(src[:90])

        print(f"Thumbnails OK:     {len(ok)}")
        print(f"Thumbnails broken: {len(broken)}")
        for s in broken[:5]:
            print(f"  BROKEN: {s}")

        placeholders = await app_page.query_selector_all(".car-thumb-placeholder")
        print(f"'No image' placeholders: {len(placeholders)}")

        # ── source icon links ─────────────────────────────────────────────
        src_links = await app_page.query_selector_all("a.src-icon")
        print(f"\nSource icon links: {len(src_links)}")
        for a in src_links[:8]:
            href = await a.get_attribute("href") or ""
            img  = await a.query_selector("img")
            title_attr = await img.get_attribute("title") if img else "?"
            nat_w = await img.evaluate("el => el.naturalWidth") if img else -1
            print(f"  {'✓' if nat_w > 0 else '✗'} [{title_attr}] {href[:80]}")

        # ── body text snippet ─────────────────────────────────────────────
        body = (await app_page.inner_text("body"))[:300]
        print(f"\nBody snippet: {body}")

        await browser.close()

asyncio.run(main())
