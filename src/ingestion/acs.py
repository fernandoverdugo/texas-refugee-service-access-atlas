from __future__ import annotations

import os

import pandas as pd
import requests

from src.config import ACS_YEAR, DFW_COUNTIES, TEXAS_STATE_FIPS


ACS_VARIABLES = {
    "NAME": "name",
    "B01003_001E": "population",
    "B05002_013E": "foreign_born_population",
    "B17001_002E": "population_below_poverty",
    "B08201_002E": "households_no_vehicle",
    "B25003_003E": "renter_occupied_households",
}


def build_acs_tract_url(
    county_fips: str,
    year: int = ACS_YEAR,
    api_key: str | None = None,
) -> tuple[str, dict[str, str]]:
    if county_fips not in DFW_COUNTIES:
        raise ValueError(f"Unsupported county FIPS: {county_fips}")

    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": ",".join(ACS_VARIABLES),
        "for": "tract:*",
        "in": f"state:{TEXAS_STATE_FIPS} county:{county_fips}",
    }

    key = api_key or os.getenv("CENSUS_API_KEY")
    if key:
        params["key"] = key

    return url, params


def parse_acs_response(
    payload: list[list[str]],
    county_fips: str,
    year: int = ACS_YEAR,
) -> pd.DataFrame:
    if not payload or len(payload) < 2:
        raise ValueError("ACS response did not contain data rows")

    frame = pd.DataFrame(payload[1:], columns=payload[0])
    required = set(ACS_VARIABLES).union({"state", "county", "tract"})
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"ACS response missing columns: {sorted(missing)}")

    frame = frame.rename(columns=ACS_VARIABLES)
    numeric = [column for column in ACS_VARIABLES.values() if column != "name"]

    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if (frame[column] < 0).any():
            raise ValueError(f"ACS estimate contains negative values: {column}")

    frame["county_name"] = DFW_COUNTIES[county_fips]
    frame["geoid"] = frame["state"] + frame["county"] + frame["tract"]
    frame["acs_year"] = year

    if frame["geoid"].duplicated().any():
        raise ValueError("ACS response contains duplicate tract GEOIDs")

    return frame[
        [
            "geoid",
            "state",
            "county",
            "county_name",
            "tract",
            "name",
            "acs_year",
            *numeric,
        ]
    ].sort_values("geoid").reset_index(drop=True)


def fetch_acs_tracts(
    county_fips: str,
    year: int = ACS_YEAR,
    api_key: str | None = None,
    timeout: int = 60,
) -> pd.DataFrame:
    url, params = build_acs_tract_url(
        county_fips=county_fips,
        year=year,
        api_key=api_key,
    )
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return parse_acs_response(response.json(), county_fips, year=year)


def fetch_dfw_acs(
    year: int = ACS_YEAR,
    api_key: str | None = None,
) -> pd.DataFrame:
    frames = [
        fetch_acs_tracts(county_fips, year=year, api_key=api_key)
        for county_fips in DFW_COUNTIES
    ]
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["county", "tract"])
        .reset_index(drop=True)
    )
