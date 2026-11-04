from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from shapely.geometry import mapping, shape
from shapely.ops import unary_union


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


def _read_temporal_accessibility() -> pd.DataFrame:
    path = DATA / "tract_temporal_accessibility.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Time-dependent accessibility is not available",
        )
    return pd.read_csv(path, dtype={"geoid": str})


def _read_temporal_service_accessibility() -> pd.DataFrame:
    path = DATA / "tract_temporal_service_type_accessibility.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Time-dependent service accessibility is not available",
        )
    return pd.read_csv(path, dtype={"geoid": str})


def _read_temporal_metadata() -> pd.DataFrame:
    path = DATA / "temporal_scenario_metadata.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Time-dependent scenario metadata is not available",
        )
    return pd.read_csv(path)


def _read_temporal_summary() -> pd.DataFrame:
    path = DATA / "temporal_accessibility_summary.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Time-dependent accessibility summary is not available",
        )
    return pd.read_csv(path)


def _read_temporal_service_summary() -> pd.DataFrame:
    path = DATA / "temporal_service_type_summary.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Time-dependent service summary is not available",
        )
    return pd.read_csv(path)


def _read_service_gap_classification() -> pd.DataFrame:
    path = DATA / "tract_service_gap_classification.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Service-gap classifications are not available",
        )
    return pd.read_csv(path, dtype={"geoid": str})


def _read_service_gap_summary() -> pd.DataFrame:
    path = DATA / "service_gap_summary.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Service-gap summary is not available",
        )
    return pd.read_csv(path)


def _read_service_gap_priority() -> pd.DataFrame:
    path = DATA / "service_gap_priority_tracts.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Service-gap priority tracts are not available",
        )
    return pd.read_csv(path, dtype={"geoid": str})


def _read_service_gap_thresholds() -> pd.DataFrame:
    path = DATA / "service_gap_thresholds.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Service-gap thresholds are not available",
        )
    return pd.read_csv(path)


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

            population = properties.get("population")
            foreign_born = properties.get("foreign_born_population")
            if population is not None and float(population) > 0:
                properties["foreign_born_share"] = (
                    float(foreign_born or 0) / float(population)
                )
            else:
                properties["foreign_born_share"] = None

    return geo




@app.get("/api/study-area")
def study_area() -> dict:
    geo = _read_geojson()
    grouped: dict[str, list] = {}

    county_by_prefix = {
        "48113": "Dallas",
        "48439": "Tarrant",
    }

    for feature in geo.get("features", []):
        properties = feature.get("properties", {})
        geoid = str(
            properties.get("geoid")
            or properties.get("GEOID")
            or ""
        ).zfill(11)
        county_name = (
            properties.get("county_name")
            or county_by_prefix.get(geoid[:5])
        )
        geometry = feature.get("geometry")

        if county_name and geometry:
            grouped.setdefault(str(county_name), []).append(shape(geometry))

    features = []
    for county_name, geometries in sorted(grouped.items()):
        county_geometry = unary_union(geometries)
        label_point = county_geometry.representative_point()

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "county_name": county_name,
                    "label_latitude": label_point.y,
                    "label_longitude": label_point.x,
                },
                "geometry": mapping(county_geometry),
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


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



@app.get("/api/time-scenarios")
def time_scenarios() -> list[dict]:
    metadata = _read_temporal_metadata().copy()
    summary = _read_temporal_summary()[
        [
            "scenario_id",
            "foreign_born_access_pct_30m",
            "foreign_born_access_pct_45m",
            "foreign_born_access_pct_60m",
        ]
    ]

    frame = metadata.merge(
        summary,
        on="scenario_id",
        how="left",
        validate="one_to_one",
    )

    frame["active_connections"] = frame["active_connections"].astype(int)
    for field in [
        "foreign_born_access_pct_30m",
        "foreign_born_access_pct_45m",
        "foreign_born_access_pct_60m",
    ]:
        frame[field] = frame[field].astype(float)

    return frame.to_dict("records")


@app.get("/api/temporal-accessibility/{scenario_id}")
def temporal_accessibility(scenario_id: str) -> list[dict]:
    frame = _read_temporal_accessibility()
    available = set(frame["scenario_id"].unique())

    if scenario_id not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown time scenario: {scenario_id}",
        )

    selected = frame.loc[
        frame["scenario_id"] == scenario_id,
        [
            "geoid",
            "scenario_id",
            "scenario_label",
            "departure_time",
            "service_date",
            "providers_within_30m",
            "providers_within_45m",
            "providers_within_60m",
        ],
    ].copy()

    selected["geoid"] = selected["geoid"].astype(str).str.zfill(11)
    for field in [
        "providers_within_30m",
        "providers_within_45m",
        "providers_within_60m",
    ]:
        selected[field] = selected[field].astype(int)

    return selected.to_dict("records")


@app.get("/api/temporal-service-accessibility/{scenario_id}/{service_type}")
def temporal_service_accessibility(
    scenario_id: str,
    service_type: str,
) -> list[dict]:
    frame = _read_temporal_service_accessibility()

    scenarios = set(frame["scenario_id"].unique())
    services = set(frame["service_type"].unique())

    if scenario_id not in scenarios:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown time scenario: {scenario_id}",
        )
    if service_type not in services:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service type: {service_type}",
        )

    selected = frame.loc[
        (frame["scenario_id"] == scenario_id)
        & (frame["service_type"] == service_type),
        [
            "geoid",
            "scenario_id",
            "scenario_label",
            "departure_time",
            "service_date",
            "service_type",
            "providers_within_30m",
            "providers_within_45m",
            "providers_within_60m",
        ],
    ].copy()

    selected["geoid"] = selected["geoid"].astype(str).str.zfill(11)
    for field in [
        "providers_within_30m",
        "providers_within_45m",
        "providers_within_60m",
    ]:
        selected[field] = selected[field].astype(int)

    return selected.to_dict("records")


@app.get("/api/temporal-summaries")
def temporal_summaries() -> dict[str, list[dict]]:
    overall = _read_temporal_summary().copy()
    service = _read_temporal_service_summary().copy()

    return {
        "overall": overall.to_dict("records"),
        "service_types": service.to_dict("records"),
    }



@app.get("/api/service-gaps/{scenario_id}/{service_type}")
def service_gaps(
    scenario_id: str,
    service_type: str,
) -> list[dict]:
    frame = _read_service_gap_classification()

    scenarios = set(frame["scenario_id"].unique())
    services = set(frame["service_type"].unique())

    if scenario_id not in scenarios:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown time scenario: {scenario_id}",
        )
    if service_type not in services:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service type: {service_type}",
        )

    columns = [
        "geoid",
        "scenario_id",
        "scenario_label",
        "departure_time",
        "service_date",
        "service_type",
        "service_label",
        "providers_within_45m",
        "providers_within_60m",
        "county_name",
        "population",
        "foreign_born_population",
        "population_below_poverty",
        "households_no_vehicle",
        "high_foreign_born_population",
        "high_population_below_poverty",
        "high_households_no_vehicle",
        "high_context_indicators",
        "elevated_context",
        "base_gap_level",
        "gap_level",
        "gap_class",
    ]

    selected = frame.loc[
        (frame["scenario_id"] == scenario_id)
        & (frame["service_type"] == service_type),
        columns,
    ].copy()

    selected["geoid"] = selected["geoid"].astype(str).str.zfill(11)

    for field in [
        "providers_within_45m",
        "providers_within_60m",
        "population",
        "foreign_born_population",
        "population_below_poverty",
        "households_no_vehicle",
        "high_context_indicators",
        "base_gap_level",
        "gap_level",
    ]:
        selected[field] = selected[field].astype(int)

    for field in [
        "high_foreign_born_population",
        "high_population_below_poverty",
        "high_households_no_vehicle",
        "elevated_context",
    ]:
        selected[field] = selected[field].astype(bool)

    return selected.to_dict("records")


@app.get("/api/service-gap-summary")
def service_gap_summary() -> list[dict]:
    frame = _read_service_gap_summary().copy()

    integer_fields = [
        "gap_level",
        "tract_count",
        "population",
        "foreign_born_population",
        "population_below_poverty",
        "households_no_vehicle",
    ]
    for field in integer_fields:
        frame[field] = frame[field].astype(int)

    return frame.to_dict("records")


@app.get("/api/service-gap-priorities/{scenario_id}/{service_type}")
def service_gap_priorities(
    scenario_id: str,
    service_type: str,
) -> list[dict]:
    frame = _read_service_gap_priority()

    scenarios = set(frame["scenario_id"].unique())
    services = set(frame["service_type"].unique())

    if scenario_id not in scenarios:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown time scenario: {scenario_id}",
        )
    if service_type not in services:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service type: {service_type}",
        )

    selected = frame.loc[
        (frame["scenario_id"] == scenario_id)
        & (frame["service_type"] == service_type)
    ].copy()

    selected["geoid"] = selected["geoid"].astype(str).str.zfill(11)
    selected["priority_rank"] = selected["priority_rank"].astype(int)
    selected["gap_level"] = selected["gap_level"].astype(int)

    return selected.sort_values("priority_rank").to_dict("records")


@app.get("/api/service-gap-thresholds")
def service_gap_thresholds() -> list[dict]:
    frame = _read_service_gap_thresholds().copy()
    frame["quantile"] = frame["quantile"].astype(float)
    frame["threshold"] = frame["threshold"].astype(float)
    return frame.to_dict("records")
