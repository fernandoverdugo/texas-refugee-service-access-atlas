import networkx as nx
import pandas as pd

from src.analysis.accessibility import calculate_accessibility
from src.analysis.network import (
    build_scheduled_transit_edges,
    gtfs_time_to_seconds,
    nearest_stops,
)


def test_gtfs_time_allows_after_midnight_hours():
    assert gtfs_time_to_seconds("25:05:00") == 90300


def test_build_scheduled_transit_edges():
    stop_times = pd.DataFrame(
        {
            "trip_id": ["T1", "T1", "T2", "T2"],
            "arrival_time": ["08:00:00", "08:10:00", "09:00:00", "09:12:00"],
            "departure_time": ["08:00:00", "08:10:00", "09:00:00", "09:12:00"],
            "stop_id": ["A", "B", "A", "B"],
            "stop_sequence": ["1", "2", "1", "2"],
        }
    )

    edges = build_scheduled_transit_edges(stop_times)
    assert len(edges) == 1
    assert edges.loc[0, "travel_seconds"] == 660
    assert edges.loc[0, "trip_observations"] == 2


def test_nearest_stops_respects_distance():
    locations = pd.DataFrame(
        {"geoid": ["x"], "latitude": [32.78], "longitude": [-96.80]}
    )
    stops = pd.DataFrame(
        {
            "stop_id": ["near", "far"],
            "stop_lat": ["32.781", "33.5"],
            "stop_lon": ["-96.801", "-97.5"],
        }
    )

    result = nearest_stops(locations, stops, "geoid", max_walk_km=1.0)
    assert result["stop_id"].tolist() == ["near"]


def test_calculate_accessibility_counts_thresholds():
    graph = nx.DiGraph()
    graph.add_edge("A", "B", weight=600)
    graph.add_edge("B", "C", weight=600)

    origins = pd.DataFrame(
        {"geoid": ["g1"], "stop_id": ["A"], "walk_seconds": [300]}
    )
    providers = pd.DataFrame(
        {
            "provider_id": ["p1", "p2"],
            "stop_id": ["B", "C"],
            "walk_seconds": [300, 300],
        }
    )

    result = calculate_accessibility(graph, origins, providers)

    assert result.loc[0, "providers_within_30m"] == 1
    assert result.loc[0, "providers_within_45m"] == 2
