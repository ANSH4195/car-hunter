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
from scrapers import cars24, spinny, olx, teambhp, nthgear, carwale

SCRAPERS = [
    ("cars24",    cars24.scrape),
    ("spinny",    spinny.scrape),
    ("olx",       olx.scrape),
    ("teambhp",   teambhp.scrape),
    ("9thgear",   nthgear.scrape),
    ("carwale",   carwale.scrape),
]


def main() -> None:
    total_found = 0
    total_new   = 0

    existing_ids = db.fetch_all_ids()
    print(f"Loaded {len(existing_ids)} existing listing IDs")

    for name, scrape_fn in SCRAPERS:
        print(f"\n── {name} ──")
        try:
            listings = scrape_fn()
            print(f"  fetched: {len(listings)}")
            valid = [c for c in listings if is_valid(c)]
            print(f"  valid:   {len(valid)}")
            new = [l for l in valid if l.listing_id() not in existing_ids]
            print(f"  new:     {len(new)}")
            for car in new:
                db.upsert(car)
                existing_ids.add(car.listing_id())
                total_new += 1
            total_found += len(valid)
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n✓ Done — {total_found} valid listings, {total_new} new upserted to Supabase")


if __name__ == "__main__":
    main()
