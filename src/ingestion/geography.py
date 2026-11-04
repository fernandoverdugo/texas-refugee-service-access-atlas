from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import geopandas as gpd
import pandas as pd
import requests


TEXAS_TRACT_URL = "https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_48_tract.zip"
STUDY_COUNTIES = {"113": "Dallas", "439": "Tarrant"}


def download_texas_tracts(
    url: str = TEXAS_TRACT_URL,
    timeout: int = 120,
) -> bytes:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    if not response.content:
        raise RuntimeError("Census TIGER tract download returned an empty response")
    return response.content


def load_study_tract_geometries(content: bytes) -> gpd.GeoDataFrame:
    with NamedTemporaryFile(suffix=".zip") as handle:
        handle.write(content)
        handle.flush()
        tracts = gpd.read_file(handle.name)

    required = {"GEOID", "STATEFP", "COUNTYFP", "TRACTCE", "geometry"}
    missing = required.difference(tracts.columns)
    if missing:
        raise ValueError(f"TIGER tract file missing columns: {sorted(missing)}")

    tracts = tracts[
        tracts["COUNTYFP"].isin(STUDY_COUNTIES)
    ][["GEOID", "STATEFP", "COUNTYFP", "TRACTCE", "geometry"]].copy()

    if tracts.empty:
        raise ValueError("No Dallas or Tarrant County tract geometries were found")
    if tracts["GEOID"].duplicated().any():
        raise ValueError("TIGER tract file contains duplicate GEOIDs")

    tracts["county_name"] = tracts["COUNTYFP"].map(STUDY_COUNTIES)
    return tracts.sort_values("GEOID").reset_index(drop=True)


def build_tract_points(
    tracts: gpd.GeoDataFrame,
    projected_crs: str = "EPSG:2276",
) -> gpd.GeoDataFrame:
    projected = tracts.to_crs(projected_crs).copy()
    projected["geometry"] = projected.geometry.representative_point()
    points = projected.to_crs("EPSG:4326")

    points["longitude"] = points.geometry.x
    points["latitude"] = points.geometry.y

    return points[
        ["GEOID", "COUNTYFP", "county_name", "longitude", "latitude", "geometry"]
    ].rename(columns={"GEOID": "geoid"})


def join_acs_to_tracts(
    tracts: gpd.GeoDataFrame,
    acs: pd.DataFrame,
) -> gpd.GeoDataFrame:
    acs = acs.copy()
    acs["geoid"] = acs["geoid"].astype(str).str.zfill(11)

    merged = tracts.rename(columns={"GEOID": "geoid"}).merge(
        acs,
        on="geoid",
        how="left",
        validate="one_to_one",
    )

    if merged["population"].isna().any():
        missing = int(merged["population"].isna().sum())
        raise ValueError(f"{missing} tract geometries did not match ACS rows")

    return gpd.GeoDataFrame(merged, geometry="geometry", crs=tracts.crs)
