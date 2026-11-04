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
    assert 'const timeSelect = document.getElementById("timeScenario");' in response.text
    assert 'let temporalSummaries = { overall: [], service_types: [] };' in response.text
    assert "Weekday morning · 8:00 AM" in response.text
    assert "Saturday midday · 1:00 PM" in response.text
    assert "Service-access gap classification" in response.text
    assert "Foreign-born share of population" in response.text
    assert "let currentServiceGaps = {};" in response.text
    assert 'fetch("/api/service-gap-summary")' in response.text
    assert 'fetch("/api/study-area")' in response.text
    assert "function renderStudyArea(studyArea)" in response.text
    assert "county-label" in response.text
    assert 'map.createPane("countyBoundaryPane");' in response.text
    assert "countyBoundaryLayer.bringToFront()" not in response.text
    assert 'fetch("/api/service-gaps/" + timeScenario + "/" + serviceType)' in response.text


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_summary():
    response = client.get("/api/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tracts"] == 1094
    assert payload["providers"] == 8
    assert payload["transit_stops"] > 8000


def test_providers():
    response = client.get("/api/providers")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 8
    assert {row["county"] for row in payload} == {"Dallas", "Tarrant"}
    assert all(row["latitude"] is not None for row in payload)
    assert all(row["longitude"] is not None for row in payload)
    assert all(row["normalized_service_types"] for row in payload)
    assert "cws_dallas" in {row["provider_id"] for row in payload}


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



def test_time_scenarios():
    response = client.get("/api/time-scenarios")

    assert response.status_code == 200
    payload = response.json()

    assert {row["scenario_id"] for row in payload} == {
        "weekday_morning",
        "weekday_midday",
        "weekday_evening",
        "weekend_midday",
    }

    by_id = {row["scenario_id"]: row for row in payload}
    assert by_id["weekday_morning"]["service_date"] == "2026-12-02"
    assert by_id["weekend_midday"]["service_date"] == "2026-12-05"
    assert by_id["weekday_midday"]["foreign_born_access_pct_45m"] > 0.16
    assert by_id["weekday_morning"]["foreign_born_access_pct_45m"] < 0.14


def test_temporal_accessibility():
    response = client.get("/api/temporal-accessibility/weekday_midday")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1094
    assert {row["scenario_id"] for row in payload} == {"weekday_midday"}
    assert all(len(row["geoid"]) == 11 for row in payload)
    assert all(
        row["providers_within_30m"]
        <= row["providers_within_45m"]
        <= row["providers_within_60m"]
        for row in payload
    )


def test_temporal_service_accessibility():
    response = client.get(
        "/api/temporal-service-accessibility/weekend_midday/immigration"
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1094
    assert {row["service_type"] for row in payload} == {"immigration"}
    assert all(
        row["providers_within_30m"]
        <= row["providers_within_45m"]
        <= row["providers_within_60m"]
        for row in payload
    )


def test_temporal_summaries():
    response = client.get("/api/temporal-summaries")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["overall"]) == 4
    assert len(payload["service_types"]) == 24


def test_unknown_temporal_scenario_returns_404():
    response = client.get("/api/temporal-accessibility/not_a_scenario")

    assert response.status_code == 404



def test_service_gap_summary():
    response = client.get("/api/service-gap-summary")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) > 100
    assert {row["gap_class"] for row in payload} == {
        "Lower gap",
        "Moderate gap",
        "High gap",
        "Severe gap",
    }

    midday_immigration = [
        row
        for row in payload
        if row["scenario_id"] == "weekday_midday"
        and row["service_type"] == "immigration"
    ]
    by_class = {row["gap_class"]: row for row in midday_immigration}

    assert by_class["Severe gap"]["tract_count"] == 189
    assert by_class["High gap"]["tract_count"] == 750


def test_service_gaps():
    response = client.get(
        "/api/service-gaps/weekday_midday/immigration"
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1094
    assert {row["gap_class"] for row in payload} <= {
        "Lower gap",
        "Moderate gap",
        "High gap",
        "Severe gap",
    }
    assert all(0 <= row["gap_level"] <= 3 for row in payload)
    assert all(0 <= row["high_context_indicators"] <= 3 for row in payload)


def test_service_gap_priorities():
    response = client.get(
        "/api/service-gap-priorities/weekday_midday/immigration"
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 25
    assert [row["priority_rank"] for row in payload] == list(range(1, 26))
    assert payload[0]["gap_class"] == "Severe gap"


def test_service_gap_thresholds():
    response = client.get("/api/service-gap-thresholds")

    assert response.status_code == 200
    payload = response.json()

    by_indicator = {row["indicator"]: row for row in payload}
    assert by_indicator["foreign_born_population"]["threshold"] == 1307.0
    assert by_indicator["population_below_poverty"]["threshold"] == 736.75
    assert by_indicator["households_no_vehicle"]["threshold"] == 128.75
    assert all(row["quantile"] == 0.75 for row in payload)


def test_unknown_service_gap_scenario_returns_404():
    response = client.get("/api/service-gaps/not_a_scenario/immigration")

    assert response.status_code == 404



def test_study_area():
    response = client.get("/api/study-area")

    assert response.status_code == 200
    payload = response.json()

    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 2

    by_county = {
        feature["properties"]["county_name"]: feature
        for feature in payload["features"]
    }

    assert set(by_county) == {"Dallas", "Tarrant"}

    for feature in by_county.values():
        properties = feature["properties"]
        assert -98.5 < properties["label_longitude"] < -96.0
        assert 31.5 < properties["label_latitude"] < 34.0
        assert feature["geometry"]["type"] in {"Polygon", "MultiPolygon"}



def test_tract_foreign_born_share():
    response = client.get("/api/tracts")

    assert response.status_code == 200
    payload = response.json()

    checked = 0
    for feature in payload["features"]:
        properties = feature["properties"]
        population = properties.get("population")
        foreign_born = properties.get("foreign_born_population")
        share = properties.get("foreign_born_share")

        if population and population > 0:
            assert share is not None
            assert 0 <= share <= 1
            assert abs(share - (foreign_born / population)) < 1e-12
            checked += 1
            if checked >= 25:
                break

    assert checked == 25
