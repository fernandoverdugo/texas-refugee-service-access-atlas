from __future__ import annotations

import re
import time
from pathlib import Path

import pandas as pd
import requests


CENSUS_GEOCODER_URL = (
    "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = (
    "texas-refugee-service-access-atlas/0.1 "
    "(https://github.com/fernandoverdugo/texas-refugee-service-access-atlas)"
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


def geocode_census(
    address: str,
    timeout: int = 60,
) -> dict[str, object]:
    for candidate in address_variants(address):
        response = requests.get(
            CENSUS_GEOCODER_URL,
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
            "geocode_source": "census",
            "geocode_query": candidate,
            "matched_address": first.get("matchedAddress"),
            "longitude": coordinates.get("x"),
            "latitude": coordinates.get("y"),
        }

    return {
        "matched": False,
        "geocode_source": None,
        "geocode_query": None,
        "matched_address": None,
        "longitude": None,
        "latitude": None,
    }


def geocode_nominatim(
    query: str,
    timeout: int = 60,
) -> dict[str, object]:
    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "us",
        },
        headers={"User-Agent": NOMINATIM_USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    if not payload:
        return {
            "matched": False,
            "geocode_source": None,
            "geocode_query": None,
            "matched_address": None,
            "longitude": None,
            "latitude": None,
        }

    first = payload[0]
    return {
        "matched": True,
        "geocode_source": "openstreetmap_nominatim",
        "geocode_query": query,
        "matched_address": first.get("display_name"),
        "longitude": float(first["lon"]),
        "latitude": float(first["lat"]),
    }


def nominatim_queries(
    record: dict[str, object],
    full_address: str,
) -> list[str]:
    candidates = [
        f'{record["organization"]}, {full_address}',
        *address_variants(full_address),
        f'{record["organization"]}, {record["city"]}, {record["state"]}',
        f'{record["location_name"]}, {record["city"]}, {record["state"]}',
    ]
    return list(dict.fromkeys(str(candidate).strip() for candidate in candidates))


def _cached_result(
    cache: pd.DataFrame | None,
    provider_id: str,
    address: str,
) -> dict[str, object] | None:
    if cache is None or cache.empty:
        return None

    required = {
        "provider_id",
        "address",
        "matched",
        "geocode_source",
        "geocode_query",
        "matched_address",
        "longitude",
        "latitude",
    }
    if not required.issubset(cache.columns):
        return None

    rows = cache[
        (cache["provider_id"] == provider_id)
        & (cache["address"] == address)
        & (cache["matched"].astype(str).str.lower() == "true")
    ]
    if rows.empty:
        return None

    row = rows.iloc[0]
    return {
        "matched": True,
        "geocode_source": row["geocode_source"],
        "geocode_query": row["geocode_query"],
        "matched_address": row["matched_address"],
        "longitude": float(row["longitude"]),
        "latitude": float(row["latitude"]),
    }


def geocode_provider_inventory(
    providers: pd.DataFrame,
    cache: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows = []

    for record in providers.to_dict("records"):
        full_address = (
            f'{record["address"]}, {record["city"]}, '
            f'{record["state"]} {record["zip"]}'
        )

        result = _cached_result(
            cache,
            record["provider_id"],
            record["address"],
        )

        if result is None:
            result = geocode_census(full_address)

        if not result["matched"]:
            for query in nominatim_queries(record, full_address):
                time.sleep(1.1)
                result = geocode_nominatim(query)
                if result["matched"]:
                    break

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
