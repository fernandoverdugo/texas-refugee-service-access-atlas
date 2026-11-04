from __future__ import annotations

import math

import networkx as nx
import pandas as pd


THRESHOLDS_MINUTES = (30, 45, 60)


def calculate_accessibility(
    graph: nx.DiGraph,
    origin_connectors: pd.DataFrame,
    provider_connectors: pd.DataFrame,
    all_geoids: list[str] | None = None,
) -> pd.DataFrame:
    required_origins = {"geoid", "stop_id", "walk_seconds"}
    required_providers = {"provider_id", "stop_id", "walk_seconds"}

    if missing := required_origins.difference(origin_connectors.columns):
        raise ValueError(f"origin connectors missing columns: {sorted(missing)}")
    if missing := required_providers.difference(provider_connectors.columns):
        raise ValueError(f"provider connectors missing columns: {sorted(missing)}")

    origin_groups = {
        geoid: group.to_dict("records")
        for geoid, group in origin_connectors.groupby("geoid")
    }

    provider_results: dict[str, dict[str, float]] = {}
    reverse = graph.reverse(copy=False)

    for provider_id, group in provider_connectors.groupby("provider_id"):
        best_to_stop: dict[str, float] = {}

        for connector in group.to_dict("records"):
            stop_id = connector["stop_id"]
            if stop_id not in reverse:
                continue

            lengths = nx.single_source_dijkstra_path_length(
                reverse,
                stop_id,
                weight="weight",
                cutoff=60 * 60,
            )
            final_walk = float(connector["walk_seconds"])

            for origin_stop, network_seconds in lengths.items():
                total = float(network_seconds) + final_walk
                previous = best_to_stop.get(origin_stop)
                if previous is None or total < previous:
                    best_to_stop[origin_stop] = total

        provider_results[provider_id] = best_to_stop

    geoids = all_geoids or sorted(origin_groups)
    rows = []

    for geoid in geoids:
        best: dict[str, float] = {}
        connectors = origin_groups.get(geoid, [])

        for provider_id, stop_distances in provider_results.items():
            for connector in connectors:
                network_and_final = stop_distances.get(connector["stop_id"])
                if network_and_final is None:
                    continue

                total = float(connector["walk_seconds"]) + network_and_final
                previous = best.get(provider_id)
                if previous is None or total < previous:
                    best[provider_id] = total

        values = list(best.values())
        record = {
            "geoid": geoid,
            "reachable_providers": len(best),
            "nearest_provider_minutes": min(values) / 60 if values else math.nan,
        }

        for threshold in THRESHOLDS_MINUTES:
            record[f"providers_within_{threshold}m"] = sum(
                value <= threshold * 60 for value in values
            )

        rows.append(record)

    return pd.DataFrame(rows).sort_values("geoid").reset_index(drop=True)
