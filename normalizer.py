"""
Gemini Flash-Lite: parse messy listing text → structured fields.
Only called when a scraper can't extract clean structured data itself.
"""
from __future__ import annotations
import json
import os
import re

import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_model = genai.GenerativeModel("gemini-2.5-flash")

_PROMPT = """Extract used car listing details from the text below.
Return ONLY valid JSON with these keys (use null if unknown):
{"make","model","variant","year","kms","fuel","transmission","color","location","price_inr"}

Text:
"""


def normalize(raw_text: str) -> dict | None:
    try:
        resp = _model.generate_content(
            _PROMPT + raw_text,
            generation_config={"response_mime_type": "application/json"},
        )
        return json.loads(resp.text)
    except Exception as e:
        print(f"[normalizer] {e}")
        return None


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
    m = re.search(r"([\d]+)\s*k(?:m)?", text)
    if m:
        val = int(m.group(1))
        return val * 1000 if val < 1000 else val
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None
