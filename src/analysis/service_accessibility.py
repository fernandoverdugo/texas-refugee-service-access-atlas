from __future__ import annotations

import pandas as pd
import networkx as nx

from src.analysis.accessibility import calculate_accessibility
from src.analysis.service_types import (
    SERVICE_TYPE_LABELS,
    normalize_provider_service_types,
)


def calculate_service_type_accessibility(
    graph: nx.DiGraph,
    origin_connectors: pd.DataFrame,
    provider_connectors: pd.DataFrame,
    providers: pd.DataFrame,
    all_geoids: list[str],
) -> pd.DataFrame:
    mapping = normalize_provider_service_types(providers)
    frames = []

    for service_type, label in SERVICE_TYPE_LABELS.items():
        provider_ids = set(
            mapping.loc[
                mapping["service_type"] == service_type,
                "provider_id",
            ]
        )

        connectors = provider_connectors[
            provider_connectors["provider_id"].isin(provider_ids)
        ].copy()

        if connectors.empty:
            continue

        access = calculate_accessibility(
            graph,
            origin_connectors,
            connectors,
            all_geoids=all_geoids,
        )
        access = access.rename(
            columns={
                "reachable_providers": "reachable_service_locations",
                "nearest_provider_minutes": "nearest_service_minutes",
                "providers_within_30m": "service_locations_within_30m",
                "providers_within_45m": "service_locations_within_45m",
                "providers_within_60m": "service_locations_within_60m",
            }
        )
        access["service_type"] = service_type
        access["service_label"] = label
        access["provider_locations"] = len(provider_ids)
        frames.append(access)

    if not frames:
        raise ValueError("No service-type accessibility outputs were produced")

    return pd.concat(frames, ignore_index=True)[
        [
            "geoid",
            "service_type",
            "service_label",
            "provider_locations",
            "reachable_service_locations",
            "nearest_service_minutes",
            "service_locations_within_30m",
            "service_locations_within_45m",
            "service_locations_within_60m",
        ]
    ].sort_values(["service_type", "geoid"]).reset_index(drop=True)
