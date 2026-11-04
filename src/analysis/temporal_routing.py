from __future__ import annotations

import heapq

import pandas as pd


def reverse_transfer_adjacency(
    transfer_edges: pd.DataFrame,
) -> dict[str, list[tuple[str, int]]]:
    required = {"from_stop_id", "to_stop_id", "walk_seconds"}
    if missing := required.difference(transfer_edges.columns):
        raise ValueError(f"transfer edges missing columns: {sorted(missing)}")

    adjacency: dict[str, list[tuple[str, int]]] = {}
    for row in transfer_edges.itertuples(index=False):
        adjacency.setdefault(str(row.to_stop_id), []).append(
            (str(row.from_stop_id), int(float(row.walk_seconds)))
        )
    return adjacency


def _relax_walking_backward(
    latest: dict[str, int],
    seeds: list[str],
    adjacency: dict[str, list[tuple[str, int]]],
    departure_seconds: int,
) -> None:
    heap = [(-latest[stop], stop) for stop in seeds]
    heapq.heapify(heap)

    while heap:
        negative_time, stop = heapq.heappop(heap)
        time = -negative_time

        if latest.get(stop) != time:
            continue

        for previous_stop, walk_seconds in adjacency.get(stop, []):
            candidate = time - walk_seconds
            if candidate < departure_seconds:
                continue
            if candidate > latest.get(previous_stop, -1):
                latest[previous_stop] = candidate
                heapq.heappush(heap, (-candidate, previous_stop))


def latest_stop_departures(
    connections: pd.DataFrame,
    transfer_edges: pd.DataFrame,
    destination_connectors: pd.DataFrame,
    departure_seconds: int,
    threshold_minutes: int,
) -> dict[str, int]:
    deadline = departure_seconds + threshold_minutes * 60
    latest: dict[str, int] = {}
    adjacency = reverse_transfer_adjacency(transfer_edges)
    seeds = []

    for row in destination_connectors.itertuples(index=False):
        latest_time = deadline - int(float(row.walk_seconds))
        if latest_time < departure_seconds:
            continue
        stop_id = str(row.stop_id)
        if latest_time > latest.get(stop_id, -1):
            latest[stop_id] = latest_time
            seeds.append(stop_id)

    _relax_walking_backward(
        latest,
        seeds,
        adjacency,
        departure_seconds,
    )

    relevant = connections[
        (connections["arrival_seconds"] <= deadline)
        & (connections["departure_seconds"] >= departure_seconds)
    ]

    for row in relevant.itertuples(index=False):
        to_stop = str(row.to_stop_id)
        if latest.get(to_stop, -1) < int(row.arrival_seconds):
            continue

        from_stop = str(row.from_stop_id)
        candidate = int(row.departure_seconds)

        if candidate > latest.get(from_stop, -1):
            latest[from_stop] = candidate
            _relax_walking_backward(
                latest,
                [from_stop],
                adjacency,
                departure_seconds,
            )

    return latest


def origin_geoids_reaching_destination(
    latest: dict[str, int],
    origin_connectors: pd.DataFrame,
    departure_seconds: int,
) -> set[str]:
    reachable = set()

    for row in origin_connectors.itertuples(index=False):
        arrival_at_stop = departure_seconds + int(float(row.walk_seconds))
        if arrival_at_stop <= latest.get(str(row.stop_id), -1):
            reachable.add(str(row.geoid))

    return reachable


def calculate_temporal_provider_access(
    connections: pd.DataFrame,
    transfer_edges: pd.DataFrame,
    origin_connectors: pd.DataFrame,
    provider_connectors: pd.DataFrame,
    all_geoids: list[str],
    scenario_id: str,
    departure_seconds: int,
    thresholds: tuple[int, ...] = (30, 45, 60),
) -> pd.DataFrame:
    provider_ids = sorted(provider_connectors["provider_id"].astype(str).unique())

    counts = {
        threshold: {str(geoid): 0 for geoid in all_geoids}
        for threshold in thresholds
    }

    for provider_id in provider_ids:
        destination = provider_connectors[
            provider_connectors["provider_id"].astype(str) == provider_id
        ]

        for threshold in thresholds:
            latest = latest_stop_departures(
                connections,
                transfer_edges,
                destination,
                departure_seconds,
                threshold,
            )
            reachable = origin_geoids_reaching_destination(
                latest,
                origin_connectors,
                departure_seconds,
            )
            for geoid in reachable:
                counts[threshold][geoid] += 1

    rows = []
    for geoid in all_geoids:
        record = {
            "geoid": str(geoid),
            "scenario_id": scenario_id,
        }
        for threshold in thresholds:
            record[f"providers_within_{threshold}m"] = counts[threshold][str(geoid)]
        rows.append(record)

    return pd.DataFrame(rows)


def calculate_temporal_service_type_access(
    connections: pd.DataFrame,
    transfer_edges: pd.DataFrame,
    origin_connectors: pd.DataFrame,
    provider_connectors: pd.DataFrame,
    provider_service_map: pd.DataFrame,
    all_geoids: list[str],
    scenario_id: str,
    departure_seconds: int,
    thresholds: tuple[int, ...] = (30, 45, 60),
) -> pd.DataFrame:
    frames = []

    for service_type, group in provider_service_map.groupby("service_type"):
        provider_ids = set(group["provider_id"].astype(str))
        connectors = provider_connectors[
            provider_connectors["provider_id"].astype(str).isin(provider_ids)
        ]
        access = calculate_temporal_provider_access(
            connections,
            transfer_edges,
            origin_connectors,
            connectors,
            all_geoids,
            scenario_id,
            departure_seconds,
            thresholds,
        )
        access["service_type"] = service_type
        frames.append(access)

    return pd.concat(frames, ignore_index=True)
