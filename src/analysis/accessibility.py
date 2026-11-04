from __future__ import annotations

import math

import networkx as nx
import pandas as pd


THRESHOLDS_MINUTES = (30, 45, 60)


def calculate_accessibility(
    graph: nx.DiGraph,
    origin_connectors: pd.DataFrame,
    provider_connectors: pd.DataFrame,
) -> pd.DataFrame:
    if origin_connectors.empty:
        raise ValueError("origin connectors are empty")
    if provider_connectors.empty:
        raise ValueError("provider connectors are empty")

    provider_by_stop = {}
    for row in provider_connectors.itertuples(index=False):
        provider_by_stop.setdefault(row.stop_id, []).append(
            (row.provider_id, float(row.walk_seconds))
        )

    rows = []

    for geoid, origin_rows in origin_connectors.groupby("geoid"):
        best = {}

        for origin in origin_rows.itertuples(index=False):
            if origin.stop_id not in graph:
                continue

            lengths = nx.single_source_dijkstra_path_length(
                graph,
                origin.stop_id,
                weight="weight",
            )

            for stop_id, network_seconds in lengths.items():
                for provider_id, final_walk in provider_by_stop.get(stop_id, []):
                    total = (
                        float(origin.walk_seconds)
                        + float(network_seconds)
                        + final_walk
                    )
                    if provider_id not in best or total < best[provider_id]:
                        best[provider_id] = total

        values = list(best.values())
        record = {
            "geoid": geoid,
            "reachable_providers": len(best),
            "nearest_provider_minutes": (
                min(values) / 60 if values else math.nan
            ),
        }

        for threshold in THRESHOLDS_MINUTES:
            record[f"providers_within_{threshold}m"] = sum(
                value <= threshold * 60 for value in values
            )

        rows.append(record)

    return pd.DataFrame(rows).sort_values("geoid").reset_index(drop=True)
