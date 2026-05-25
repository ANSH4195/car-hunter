"""Hard-delete listings that no longer pass current filters."""
from __future__ import annotations
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from db import _get, hard_delete
from filters import is_valid
from scrapers.base import CarListing


def main(dry_run: bool = False) -> None:
    db = _get()
    rows = db.table("listings").select("*").execute().data or []
    print(f"Total listings in DB: {len(rows)}")

    to_delete: list[str] = []
    for row in rows:
        car = CarListing(
            make=row.get("make") or "",
            model=row.get("model") or "",
            variant=row.get("variant") or "",
            year=row.get("year") or 0,
            kms=row.get("kms") or 0,
            fuel=row.get("fuel") or "",
            transmission=row.get("transmission") or "",
            color=row.get("color") or "",
            location=row.get("location") or "",
            state=row.get("state") or "",
            price=row.get("price") or 0,
            image_url=row.get("image_url") or "",
            source_name="",
            source_url="",
        )
        if not is_valid(car):
            to_delete.append(row["id"])
            print(f"  {'[dry]' if dry_run else 'DELETE'} {row['make']} {row['model']} {row['year']} {row['kms']}km ₹{row['price']}")

    if not to_delete:
        print("Nothing to delete.")
        return

    print(f"\n{'Would delete' if dry_run else 'Deleting'} {len(to_delete)} listing(s).")
    if dry_run:
        return

    for car_id in to_delete:
        hard_delete(car_id)
    print("Done.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
