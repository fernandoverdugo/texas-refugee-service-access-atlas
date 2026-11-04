import networkx as nx
import pandas as pd

from src.optimization.facility_location import (
    candidate_access_times,
    score_candidates,
    select_best_candidate,
)


def test_candidate_access_times():
    graph = nx.DiGraph()
    graph.add_edge("A", "B", weight=600)
    graph.add_edge("B", "C", weight=600)

    origins = pd.DataFrame(
        {
            "geoid": ["g1", "g2"],
            "stop_id": ["A", "B"],
            "walk_seconds": [0, 0],
        }
    )
    candidates = pd.DataFrame(
        {
            "geoid": ["c1"],
            "stop_id": ["C"],
            "walk_seconds": [0],
        }
    )

    result = candidate_access_times(
        graph,
        origins,
        candidates,
        cutoff_minutes=30,
    )

    assert set(result["origin_geoid"]) == {"g1", "g2"}
    assert result.loc[result["origin_geoid"] == "g1", "travel_minutes"].iloc[0] == 20


def test_score_candidates_prioritizes_newly_covered_weight():
    access = pd.DataFrame(
        {
            "candidate_geoid": ["c1", "c1", "c2"],
            "origin_geoid": ["g1", "g2", "g2"],
            "travel_minutes": [20, 30, 15],
        }
    )
    context = pd.DataFrame(
        {
            "geoid": ["g1", "g2"],
            "foreign_born_population": [100, 80],
            "population": [500, 400],
            "households_no_vehicle": [20, 30],
        }
    )
    baseline = pd.DataFrame(
        {
            "geoid": ["g1", "g2"],
            "providers_within_45m": [0, 0],
        }
    )

    scored = score_candidates(access, context, baseline)
    best = select_best_candidate(scored)

    assert best["candidate_geoid"] == "c1"
    assert best["newly_covered_weight"] == 180
    assert best["newly_covered_tracts"] == 2


def test_score_excludes_already_served_tracts():
    access = pd.DataFrame(
        {
            "candidate_geoid": ["c1", "c1"],
            "origin_geoid": ["g1", "g2"],
            "travel_minutes": [20, 20],
        }
    )
    context = pd.DataFrame(
        {
            "geoid": ["g1", "g2"],
            "foreign_born_population": [100, 80],
            "population": [500, 400],
            "households_no_vehicle": [20, 30],
        }
    )
    baseline = pd.DataFrame(
        {
            "geoid": ["g1", "g2"],
            "providers_within_45m": [1, 0],
        }
    )

    scored = score_candidates(access, context, baseline)

    assert scored.loc[0, "newly_covered_weight"] == 80
    assert scored.loc[0, "newly_covered_tracts"] == 1
