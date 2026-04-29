"""Supabase layer — upsert listings, soft-delete, fetch for UI."""
from __future__ import annotations
import json
import os
from datetime import date

from supabase import create_client, Client
from scrapers.base import CarListing

_client: Client | None = None


def _get() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_KEY"],
        )
    return _client


# ── write ──────────────────────────────────────────────────────────────────

def upsert(car: CarListing) -> None:
    db = _get()
    car_id = car.listing_id()

    # Fetch existing row to merge sources
    existing = db.table("listings").select("sources,price,image_url").eq("id", car_id).execute()

    if existing.data:
        row = existing.data[0]
        sources: dict = row.get("sources") or {}
        sources[car.source_name] = {"url": car.source_url, "price": car.price}
        best_price = min(car.price, row.get("price") or car.price)
        image_url  = row.get("image_url") or car.image_url
        db.table("listings").update({
            "sources":   sources,
            "price":     best_price,
            "image_url": image_url or car.image_url,
        }).eq("id", car_id).execute()
    else:
        db.table("listings").insert({
            "id":           car_id,
            "make":         car.make,
            "model":        car.model,
            "variant":      car.variant,
            "year":         car.year,
            "kms":          car.kms,
            "fuel":         car.fuel,
            "transmission": car.transmission,
            "color":        car.color,
            "location":     car.location,
            "price":        car.price,
            "image_url":    car.image_url,
            "sources":      {car.source_name: {"url": car.source_url, "price": car.price}},
            "first_seen":   date.today().isoformat(),
            "is_active":    True,
        }).execute()


def soft_delete(car_id: str) -> None:
    _get().table("listings").update({"is_active": False}).eq("id", car_id).execute()


def hard_delete(car_id: str) -> None:
    _get().table("listings").delete().eq("id", car_id).execute()


# ── read ───────────────────────────────────────────────────────────────────

def fetch_active() -> list[dict]:
    result = (
        _get()
        .table("listings")
        .select("*")
        .eq("is_active", True)
        .order("first_seen", desc=True)
        .execute()
    )
    return result.data or []
