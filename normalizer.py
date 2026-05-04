"""Regex helpers for parsing price and odometer strings from listing text."""
from __future__ import annotations
import re


def parse_price(text: str) -> int | None:
    text = text.replace(",", "").replace("₹", "").replace("Rs.", "").strip()
    m = re.search(r"([\d.]+)\s*[Ll]akh", text)
    if m:
        return int(float(m.group(1)) * 100_000)
    m = re.search(r"([\d.]+)\s*[Cc]r", text)
    if m:
        return int(float(m.group(1)) * 10_000_000)
    m = re.search(r"\d+", text.replace(" ", ""))
    if m:
        val = int(m.group())
        return val * 100_000 if val < 1000 else val
    return None


def parse_kms(text: str) -> int | None:
    text = text.lower().replace(",", "")
    m = re.search(r"([\d]+(?:\.[\d]+)?)\s*k(?:m)?", text)
    if m:
        val = float(m.group(1))
        return int(val * 1000) if val < 1000 else int(val)
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None
