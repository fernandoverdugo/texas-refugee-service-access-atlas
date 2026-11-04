from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response


BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "processed"
STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Texas Refugee Service Access Atlas",
    version="0.1.0",
    description="Interactive accessibility atlas for refugee-relevant services in Dallas and Tarrant Counties.",
)


def _read_accessibility() -> pd.DataFrame:
    path = DATA / "tract_service_accessibility.csv"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Accessibility data are not available")
    return pd.read_csv(path, dtype={"geoid": str})


def _read_providers() -> pd.DataFrame:
    path = DATA / "provider_locations.csv"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Provider locations are not available")
    return pd.read_csv(path, dtype={"zip": str})


def _read_geojson() -> dict:
    path = DATA / "tracts_dfw.geojson"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Tract geometry is not available")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_facility_summary() -> pd.DataFrame:
    path = DATA / "facility_location_summary.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Facility-location optimization is not available",
        )
    return pd.read_csv(path, dtype={"candidate_geoid": str})


@app.head("/")
def head_root() -> Response:
    return Response(status_code=200)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    path = STATIC / "index.html"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Atlas interface is not available")
    return path.read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/summary")
def summary() -> dict:
    path = DATA / "accessibility_summary.csv"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Accessibility summary is not available")
    row = pd.read_csv(path).iloc[0].to_dict()
    return {key: int(value) for key, value in row.items()}


@app.get("/api/providers")
def providers() -> list[dict]:
    frame = _read_providers()
    columns = [
        "provider_id",
        "organization",
        "location_name",
        "address",
        "city",
        "county",
        "service_categories",
        "longitude",
        "latitude",
        "geocode_source",
    ]
    return frame[columns].to_dict("records")


@app.get("/api/tracts")
def tracts() -> dict:
    geo = _read_geojson()
    access = _read_accessibility().copy()
    access["geoid"] = access["geoid"].astype(str).str.zfill(11)
    lookup = access.set_index("geoid").to_dict("index")

    for feature in geo.get("features", []):
        properties = feature.setdefault("properties", {})
        geoid = str(
            properties.get("geoid")
            or properties.get("GEOID")
            or ""
        ).zfill(11)
        if geoid in lookup:
            properties.update(lookup[geoid])
            properties["geoid"] = geoid

    return geo



@app.get("/api/facility-location")
def facility_location() -> dict:
    summary = _read_facility_summary().iloc[0].to_dict()

    integer_fields = {
        "threshold_minutes",
        "newly_covered_foreign_born_population",
        "newly_covered_population",
        "newly_covered_no_vehicle_households",
        "newly_covered_tracts",
        "baseline_covered_foreign_born_population",
        "optimized_covered_foreign_born_population",
        "total_foreign_born_population",
    }
    float_fields = {
        "longitude",
        "latitude",
        "baseline_coverage_pct",
        "optimized_coverage_pct",
        "coverage_gain_pct_points",
    }

    for field in integer_fields:
        summary[field] = int(summary[field])
    for field in float_fields:
        summary[field] = float(summary[field])

    summary["candidate_geoid"] = str(summary["candidate_geoid"]).zfill(11)
    return summary
