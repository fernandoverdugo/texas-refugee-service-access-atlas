from fastapi.testclient import TestClient

from src.api.app import app


client = TestClient(app)


def test_atlas_root():
    response = client.get("/")

    assert response.status_code == 200
    assert "Texas Refugee Service Access Atlas" in response.text
    assert "Scheduled-transit accessibility" in response.text


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_summary():
    response = client.get("/api/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tracts"] == 1094
    assert payload["providers"] == 7
    assert payload["transit_stops"] > 8000


def test_providers():
    response = client.get("/api/providers")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 7
    assert {row["county"] for row in payload} == {"Dallas", "Tarrant"}
    assert all(row["latitude"] is not None for row in payload)
    assert all(row["longitude"] is not None for row in payload)


def test_tracts():
    response = client.get("/api/tracts")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 1094

    first = payload["features"][0]["properties"]
    assert "geoid" in first
    assert "providers_within_45m" in first
    assert "foreign_born_population" in first



def test_facility_location():
    response = client.get("/api/facility-location")

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidate_geoid"] == "48113003102"
    assert payload["county_name"] == "Dallas"
    assert payload["threshold_minutes"] == 45
    assert payload["newly_covered_foreign_born_population"] == 64363
    assert payload["optimized_coverage_pct"] > payload["baseline_coverage_pct"]
