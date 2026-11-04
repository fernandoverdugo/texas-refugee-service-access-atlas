from pathlib import Path

from src.ingestion.geocoding import geocode_provider_inventory, save_geocoded_providers
from src.ingestion.providers import load_provider_inventory


INPUT = Path("data/processed/provider_inventory.csv")
OUTPUT = Path("data/processed/provider_locations.csv")


def main() -> None:
    providers = load_provider_inventory(INPUT)
    geocoded = geocode_provider_inventory(providers)
    save_geocoded_providers(geocoded, OUTPUT)

    print(
        {
            "providers": len(geocoded),
            "matched": int(geocoded["matched"].sum()),
            "unmatched": int((~geocoded["matched"]).sum()),
        }
    )


if __name__ == "__main__":
    main()
