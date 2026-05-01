from scrapers.base import CarListing

TARGET: dict[str, list[str]] = {
    "audi":       ["a3", "q3", "q5", "q7"],
    "volkswagen": ["tiguan"],
    "skoda":      ["octavia"],
    "jeep":       ["compass"],
}

MIN_YEAR   = 2017
MAX_KMS    = 150_000
MAX_PRICE  = 2_500_000
FUEL       = "diesel"


def is_valid(car: CarListing) -> bool:
    if car.fuel.lower() != FUEL:
        return False
    if car.year < MIN_YEAR:
        return False
    if car.kms >= MAX_KMS:
        return False
    if car.price > MAX_PRICE:
        return False

    make  = car.make.lower().strip()
    model = car.model.lower().strip()

    if make not in TARGET:
        return False
    if not any(model == t or model.startswith(t) for t in TARGET[make]):
        return False

    # Jeep Compass: pre-2022 must be Limited Plus variant
    if make == "jeep" and "compass" in model:
        if car.year < 2022 and "limited plus" not in car.variant.lower():
            return False

    return True
