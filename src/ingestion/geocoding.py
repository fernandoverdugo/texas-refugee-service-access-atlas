from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests


GEOCODER_URL = (
    "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
)


def geocode_address(
    address: str,
    timeout: int = 60,
) -> dict[str, object]:
    response = requests.get(
        GEOCODER_URL,
        params={
            "address": address,
            "benchmark": "Public_AR_Current",
            "format": "json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    matches = payload.get("result", {}).get("addressMatches", [])
    if not matches:
        return {
            "matched": False,
            "matched_address": None,
            "longitude": None,
            "latitude": None,
        }

    first = matches[0]
    coordinates = first.get("coordinates", {})
    return {
        "matched": True,
        "matched_address": first.get("matchedAddress"),
        "longitude": coordinates.get("x"),
        "latitude": coordinates.get("y"),
    }


def geocode_provider_inventory(
    providers: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for record in providers.to_dict("records"):
        full_address = (
            f'{record["address"]}, {record["city"]}, '
            f'{record["state"]} {record["zip"]}'
        )
        result = geocode_address(full_address)
        rows.append({**record, **result})

    frame = pd.DataFrame(rows)

    if not frame["provider_id"].is_unique:
        raise ValueError("Geocoded provider inventory contains duplicate provider IDs")

    return frame


def save_geocoded_providers(
    providers: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    providers.to_csv(path, index=False)
    return path
