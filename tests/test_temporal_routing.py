import pandas as pd

from src.analysis.temporal_routing import (
    calculate_temporal_provider_access,
    latest_stop_departures,
    origin_geoids_reaching_destination,
)


def test_schedule_rejects_missed_departure():
    connections = pd.DataFrame(
        {
            "from_stop_id": ["A"],
            "to_stop_id": ["B"],
            "departure_seconds": [8 * 3600 + 5 * 60],
            "arrival_seconds": [8 * 3600 + 20 * 60],
        }
    )
    transfers = pd.DataFrame(
        columns=["from_stop_id", "to_stop_id", "walk_seconds"]
    )
    destination = pd.DataFrame(
        {
            "provider_id": ["p1"],
            "stop_id": ["B"],
            "walk_seconds": [0],
        }
    )

    latest = latest_stop_departures(
        connections,
        transfers,
        destination,
        departure_seconds=8 * 3600,
        threshold_minutes=30,
    )

    origins = pd.DataFrame(
        {
            "geoid": ["early", "late"],
            "stop_id": ["A", "A"],
            "walk_seconds": [4 * 60, 6 * 60],
        }
    )
    reachable = origin_geoids_reaching_destination(
        latest,
        origins,
        departure_seconds=8 * 3600,
    )

    assert "early" in reachable
    assert "late" not in reachable


def test_walking_transfer_can_connect_to_scheduled_trip():
    connections = pd.DataFrame(
        {
            "from_stop_id": ["B"],
            "to_stop_id": ["C"],
            "departure_seconds": [8 * 3600 + 10 * 60],
            "arrival_seconds": [8 * 3600 + 20 * 60],
        }
    )
    transfers = pd.DataFrame(
        {
            "from_stop_id": ["A"],
            "to_stop_id": ["B"],
            "walk_seconds": [5 * 60],
        }
    )
    origins = pd.DataFrame(
        {
            "geoid": ["g1"],
            "stop_id": ["A"],
            "walk_seconds": [0],
        }
    )
    providers = pd.DataFrame(
        {
            "provider_id": ["p1"],
            "stop_id": ["C"],
            "walk_seconds": [5 * 60],
        }
    )

    result = calculate_temporal_provider_access(
        connections,
        transfers,
        origins,
        providers,
        all_geoids=["g1"],
        scenario_id="morning",
        departure_seconds=8 * 3600,
    )

    assert result.loc[0, "providers_within_30m"] == 1
    assert result.loc[0, "providers_within_45m"] == 1
    assert result.loc[0, "providers_within_60m"] == 1
