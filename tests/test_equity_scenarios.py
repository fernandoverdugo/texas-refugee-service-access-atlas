import pandas as pd

from src.optimization.facility_location import (
    score_candidates,
    summarize_objective_scenario,
)


def test_summarize_objective_scenario_reports_gain():
    scored = pd.DataFrame(
        {
            "candidate_geoid": ["c1"],
            "newly_covered_weight": [80],
            "newly_covered_population": [400],
            "newly_covered_foreign_born_population": [80],
            "newly_covered_population_below_poverty": [50],
            "newly_covered_no_vehicle_households": [30],
            "newly_covered_tracts": [1],
        }
    )
    context = pd.DataFrame(
        {
            "geoid": ["g1", "g2"],
            "foreign_born_population": [100, 80],
            "population": [500, 400],
            "population_below_poverty": [60, 50],
            "households_no_vehicle": [20, 30],
        }
    )
    baseline = pd.DataFrame(
        {
            "geoid": ["g1", "g2"],
            "providers_within_45m": [1, 0],
        }
    )
    points = pd.DataFrame(
        {
            "geoid": ["c1"],
            "county_name": ["Dallas"],
            "longitude": [-96.8],
            "latitude": [32.8],
        }
    )

    summary = summarize_objective_scenario(
        scored,
        tract_context=context,
        baseline_access=baseline,
        tract_points=points,
        objective="foreign_born_population",
    )

    assert summary["candidate_geoid"] == "c1"
    assert summary["baseline_covered_objective"] == 100
    assert summary["optimized_covered_objective"] == 180
    assert summary["optimized_coverage_pct"] == 1.0


def test_population_objective_can_change_candidate_ranking():
    access = pd.DataFrame(
        {
            "candidate_geoid": ["c1", "c2"],
            "origin_geoid": ["g1", "g2"],
            "travel_minutes": [20, 20],
        }
    )
    context = pd.DataFrame(
        {
            "geoid": ["g1", "g2"],
            "foreign_born_population": [200, 50],
            "population": [300, 900],
            "population_below_poverty": [40, 400],
            "households_no_vehicle": [10, 80],
        }
    )
    baseline = pd.DataFrame(
        {
            "geoid": ["g1", "g2"],
            "providers_within_45m": [0, 0],
        }
    )

    foreign_scored = score_candidates(
        access,
        context,
        baseline,
        weight_column="foreign_born_population",
    )
    population_scored = score_candidates(
        access,
        context,
        baseline,
        weight_column="population",
    )

    assert foreign_scored.iloc[0]["candidate_geoid"] == "c1"
    assert population_scored.iloc[0]["candidate_geoid"] == "c2"
