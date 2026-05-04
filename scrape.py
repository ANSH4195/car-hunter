"""
Main entry point — runs all scrapers, filters results, upserts to Supabase.
Run locally: python scrape.py
Run via GitHub Actions: triggered by cron at 04:30 UTC (10:00 AM IST)
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from filters import is_valid
import db
from scrapers import cars24, spinny, olx, teambhp, nthgear, carwale, cardekho

SCRAPERS = [
    ("cars24",    cars24.scrape),
    ("spinny",    spinny.scrape),
    ("olx",       olx.scrape),
    ("teambhp",   teambhp.scrape),
    ("9thgear",   nthgear.scrape),
    ("carwale",   carwale.scrape),
    ("cardekho",  cardekho.scrape),
]


def main() -> None:
    total_found   = 0
    total_upserted = 0

    for name, scrape_fn in SCRAPERS:
        print(f"\n── {name} ──")
        try:
            listings = scrape_fn()
            print(f"  fetched: {len(listings)}")
            valid = [c for c in listings if is_valid(c)]
            print(f"  valid:   {len(valid)}")
            for car in valid:
                db.upsert(car)
                total_upserted += 1
            total_found += len(valid)
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n✓ Done — {total_found} valid listings, {total_upserted} upserted to Supabase")


if __name__ == "__main__":
    main()
