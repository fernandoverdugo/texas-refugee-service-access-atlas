from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "provider_id",
    "organization",
    "location_name",
    "address",
    "city",
    "state",
    "zip",
    "county",
    "service_categories",
    "refugee_specific",
    "source_url",
    "source_type",
    "verified_on",
    "notes",
}

ALLOWED_COUNTIES = {"Dallas", "Tarrant"}


def load_provider_inventory(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"zip": str})

    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Provider inventory missing columns: {sorted(missing)}")

    if frame.empty:
        raise ValueError("Provider inventory must contain at least one location")
    if frame["provider_id"].duplicated().any():
        raise ValueError("Provider inventory contains duplicate provider_id values")
    if frame["address"].isna().any() or frame["source_url"].isna().any():
        raise ValueError("Provider inventory requires an address and source URL")
    if not set(frame["county"]).issubset(ALLOWED_COUNTIES):
        raise ValueError("Provider inventory contains locations outside the initial study counties")
    if not frame["state"].eq("TX").all():
        raise ValueError("Provider inventory contains a non-Texas location")
    if not frame["source_url"].str.startswith("http").all():
        raise ValueError("Provider source URLs must be absolute HTTP(S) URLs")

    frame["verified_on"] = pd.to_datetime(frame["verified_on"], errors="raise")
    frame["refugee_specific"] = frame["refugee_specific"].astype(bool)

    return frame.sort_values(["county", "organization", "location_name"]).reset_index(drop=True)
