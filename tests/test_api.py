from fastapi.testclient import TestClient

from src.api.app import app


client = TestClient(app)


def test_atlas_root():
    response = client.get("/")

    assert response.status_code == 200
    assert "Texas Refugee Service Access Atlas" in response.text
    assert "Scheduled-transit accessibility" in response.text
    assert "Planning objective" in response.text
    assert "Population below poverty" in response.text
    assert 'let facilityScenarios = [];' in response.text
    assert 'const scenarioSelect = document.getElementById("scenarioObjective");' in response.text
    assert 'const serviceSelect = document.getElementById("serviceType");' in response.text
    assert 'let currentServiceAccess = {};' in response.text
    assert "Immigration &amp; legal support" in response.text


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
    assert all(row["normalized_service_types"] for row in payload)


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



def test_facility_location_scenarios():
    response = client.get("/api/facility-location/scenarios")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 4
    assert {row["scenario_id"] for row in payload} == {
        "foreign_born_population",
        "population",
        "households_no_vehicle",
        "population_below_poverty",
    }

    by_id = {row["scenario_id"]: row for row in payload}

    assert by_id["foreign_born_population"]["candidate_geoid"] == "48113003102"
    assert by_id["population"]["candidate_geoid"] == "48113003102"
    assert by_id["households_no_vehicle"]["candidate_geoid"] == "48113003102"
    assert by_id["population_below_poverty"]["candidate_geoid"] == "48113008701"

    assert by_id["households_no_vehicle"]["coverage_gain_pct_points"] > 0.09
    assert by_id["population_below_poverty"]["coverage_gain_pct_points"] > 0.09



def test_service_types():
    response = client.get("/api/service-types")

    assert response.status_code == 200
    payload = response.json()

    assert {row["service_type"] for row in payload} == {
        "resettlement_case_management",
        "employment",
        "education",
        "health",
        "immigration",
        "cash_benefits",
    }

    by_type = {row["service_type"]: row for row in payload}
    assert by_type["resettlement_case_management"]["provider_locations"] == 7
    assert by_type["immigration"]["provider_locations"] == 3
    assert by_type["immigration"]["foreign_born_45m_access_pct"] < 0.25


def test_service_accessibility():
    response = client.get("/api/service-accessibility/immigration")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1094
    assert {row["service_type"] for row in payload} == {"immigration"}
    assert all(len(row["geoid"]) == 11 for row in payload)
    assert all(
        row["service_locations_within_30m"]
        <= row["service_locations_within_45m"]
        <= row["service_locations_within_60m"]
        for row in payload
    )


def test_unknown_service_accessibility_returns_404():
    response = client.get("/api/service-accessibility/not_a_service")

    assert response.status_code == 404
