from scrapers.base import CarListing

# None = any model accepted; list = only those model prefixes accepted
TARGET: dict[str, list[str] | None] = {
    "audi":          ["q"],          # SUVs only (Q3, Q5, Q7, Q8…); excludes A-series sedans
    "bmw":           ["x"],          # SUVs only (X1, X3, X5, X7…); excludes 3/5/7-series sedans
    "mercedes-benz": ["g"],          # SUVs only (GLA, GLB, GLC, GLE, GLS, G-Class); excludes C/E/S-class sedans
    "volvo":         None,          # any model
    "volkswagen":    ["tiguan"],
    "skoda":         ["kodiaq"],
    "jeep":          ["compass"],
    "ford":          ["endeavour"],
    "mitsubishi":    ["pajero sport"],
}

CITY_STATE: dict[str, str] = {
    "bangalore":  "Karnataka",
    "mysore":     "Karnataka",
    "mangalore":  "Karnataka",
    "hubli":      "Karnataka",
    "bhopal":     "Madhya Pradesh",
    "indore":     "Madhya Pradesh",
    "gwalior":    "Madhya Pradesh",
    "jabalpur":   "Madhya Pradesh",
}

MIN_YEAR   = 2017
MAX_KMS    = 110_000
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

    allowed = TARGET[make]
    if allowed is not None and not any(model == t or model.startswith(t) for t in allowed):
        return False

    return True
