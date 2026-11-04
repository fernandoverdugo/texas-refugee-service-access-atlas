from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests


GEOCODER_URL = (
    "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
)


def address_variants(address: str) -> list[str]:
    candidates = [address]

    without_unit = re.sub(
        r",\s*(suite|ste\.?|unit|#)\s*[^,]+",
        "",
        address,
        flags=re.IGNORECASE,
    )
    candidates.append(without_unit)

    expanded = re.sub(r"\bW\b", "West", without_unit)
    expanded = re.sub(r"\bE\b", "East", expanded)
    expanded = re.sub(r"\bN\b", "North", expanded)
    expanded = re.sub(r"\bS\b", "South", expanded)
    candidates.append(expanded)

    directionless = re.sub(
        r"\b(?:W|E|N|S|West|East|North|South)\s+",
        "",
        expanded,
        flags=re.IGNORECASE,
    )
    candidates.append(directionless)

    return list(dict.fromkeys(candidate.strip() for candidate in candidates))


def geocode_address(
    address: str,
    timeout: int = 60,
) -> dict[str, object]:
    for candidate in address_variants(address):
        response = requests.get(
            GEOCODER_URL,
            params={
                "address": candidate,
                "benchmark": "Public_AR_Current",
                "format": "json",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()

        matches = payload.get("result", {}).get("addressMatches", [])
        if not matches:
            continue

        first = matches[0]
        coordinates = first.get("coordinates", {})
        return {
            "matched": True,
            "geocode_query": candidate,
            "matched_address": first.get("matchedAddress"),
            "longitude": coordinates.get("x"),
            "latitude": coordinates.get("y"),
        }

    return {
        "matched": False,
        "geocode_query": None,
        "matched_address": None,
        "longitude": None,
        "latitude": None,
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
