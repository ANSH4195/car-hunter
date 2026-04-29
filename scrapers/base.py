from __future__ import annotations
import hashlib
from dataclasses import dataclass


@dataclass
class CarListing:
    make: str
    model: str
    variant: str
    year: int
    kms: int
    fuel: str
    transmission: str
    color: str
    location: str
    price: int
    image_url: str
    source_name: str
    source_url: str

    def listing_id(self) -> str:
        kms_bucket = round(self.kms / 5000) * 5000
        raw = f"{self.make}|{self.model}|{self.variant}|{self.year}|{self.color}|{self.transmission}|{kms_bucket}"
        return hashlib.sha256(raw.lower().strip().encode()).hexdigest()[:20]

    def display_name(self) -> str:
        return f"{self.year} {self.make} {self.model}"
