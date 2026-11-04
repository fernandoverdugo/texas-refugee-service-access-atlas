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


def _read_facility_scenarios() -> pd.DataFrame:
    path = DATA / "facility_location_scenarios.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Equity-aware facility scenarios are not available",
        )
    return pd.read_csv(path, dtype={"candidate_geoid": str})


def _read_service_type_accessibility() -> pd.DataFrame:
    path = DATA / "tract_service_type_accessibility.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Service-type accessibility is not available",
        )
    return pd.read_csv(path, dtype={"geoid": str})


def _read_service_type_summary() -> pd.DataFrame:
    path = DATA / "service_type_accessibility_summary.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Service-type accessibility summary is not available",
        )
    return pd.read_csv(path)


def _read_provider_service_types() -> pd.DataFrame:
    path = DATA / "provider_service_types.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Provider service types are not available",
        )
    return pd.read_csv(path, dtype={"provider_id": str})


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
    frame = _read_providers().merge(
        _read_provider_service_types(),
        on="provider_id",
        how="left",
        validate="one_to_one",
    )
    columns = [
        "provider_id",
        "organization",
        "location_name",
        "address",
        "city",
        "county",
        "service_categories",
        "normalized_service_types",
        "normalized_service_labels",
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



@app.get("/api/facility-location/scenarios")
def facility_location_scenarios() -> list[dict]:
    frame = _read_facility_scenarios().copy()

    integer_fields = [
        "threshold_minutes",
        "newly_covered_objective",
        "newly_covered_population",
        "newly_covered_foreign_born_population",
        "newly_covered_population_below_poverty",
        "newly_covered_no_vehicle_households",
        "newly_covered_tracts",
        "baseline_covered_objective",
        "optimized_covered_objective",
        "total_objective",
    ]
    float_fields = [
        "longitude",
        "latitude",
        "baseline_coverage_pct",
        "optimized_coverage_pct",
        "coverage_gain_pct_points",
    ]

    for field in integer_fields:
        frame[field] = frame[field].astype(int)
    for field in float_fields:
        frame[field] = frame[field].astype(float)

    frame["candidate_geoid"] = frame["candidate_geoid"].astype(str).str.zfill(11)
    return frame.to_dict("records")



@app.get("/api/service-types")
def service_types() -> list[dict]:
    frame = _read_service_type_summary().copy()
    frame["provider_locations"] = frame["provider_locations"].astype(int)
    frame["tracts_with_45m_access"] = frame["tracts_with_45m_access"].astype(int)
    frame["foreign_born_population_with_45m_access"] = frame[
        "foreign_born_population_with_45m_access"
    ].astype(int)
    frame["foreign_born_45m_access_pct"] = frame[
        "foreign_born_45m_access_pct"
    ].astype(float)
    return frame.to_dict("records")


@app.get("/api/service-accessibility/{service_type}")
def service_accessibility(service_type: str) -> list[dict]:
    frame = _read_service_type_accessibility()
    available = set(frame["service_type"].unique())

    if service_type not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service type: {service_type}",
        )

    selected = frame.loc[
        frame["service_type"] == service_type,
        [
            "geoid",
            "service_type",
            "service_label",
            "provider_locations",
            "reachable_service_locations",
            "nearest_service_minutes",
            "service_locations_within_30m",
            "service_locations_within_45m",
            "service_locations_within_60m",
        ],
    ].copy()

    integer_fields = [
        "provider_locations",
        "reachable_service_locations",
        "service_locations_within_30m",
        "service_locations_within_45m",
        "service_locations_within_60m",
    ]
    for field in integer_fields:
        selected[field] = selected[field].astype(int)

    selected["geoid"] = selected["geoid"].astype(str).str.zfill(11)
    selected = selected.astype(object).where(pd.notna(selected), None)
    return selected.to_dict("records")
