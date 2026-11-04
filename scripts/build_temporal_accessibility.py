from pathlib import Path

import pandas as pd

from src.analysis.service_types import normalize_provider_service_types
from src.analysis.temporal_routing import (
    aggregate_provider_reachability,
    aggregate_service_type_reachability,
    calculate_provider_reachability_matrix,
)
from src.ingestion.gtfs import DART_GTFS_URL
from src.ingestion.multimodal_gtfs import TRINITY_GTFS_URL, download_zip
from src.ingestion.temporal_gtfs import (
    build_active_connections,
    namespace_temporal_feed,
    select_common_service_date,
)


PROCESSED = Path("data/processed")

SCENARIOS = [
    {
        "scenario_id": "weekday_morning",
        "scenario_label": "Weekday morning",
        "weekday": 2,
        "departure_time": "08:00",
        "departure_seconds": 8 * 3600,
    },
    {
        "scenario_id": "weekday_midday",
        "scenario_label": "Weekday midday",
        "weekday": 2,
        "departure_time": "13:00",
        "departure_seconds": 13 * 3600,
    },
    {
        "scenario_id": "weekday_evening",
        "scenario_label": "Weekday evening",
        "weekday": 2,
        "departure_time": "18:00",
        "departure_seconds": 18 * 3600,
    },
    {
        "scenario_id": "weekend_midday",
        "scenario_label": "Saturday midday",
        "weekday": 5,
        "departure_time": "13:00",
        "departure_seconds": 13 * 3600,
    },
]

THRESHOLDS = (30, 45, 60)


def build_summary(
    access: pd.DataFrame,
    context: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    merged = access.merge(
        context[
            [
                "geoid",
                "population",
                "foreign_born_population",
                "population_below_poverty",
                "households_no_vehicle",
            ]
        ],
        on="geoid",
        how="left",
        validate="many_to_one",
    )

    totals = {
        "population": float(context["population"].sum()),
        "foreign_born_population": float(
            context["foreign_born_population"].sum()
        ),
    }

    rows = []
    for keys, group in merged.groupby(group_columns, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)

        record = dict(zip(group_columns, keys))

        for threshold in THRESHOLDS:
            mask = group[f"providers_within_{threshold}m"] > 0
            record[f"tracts_within_{threshold}m"] = int(mask.sum())
            record[f"population_within_{threshold}m"] = int(
                group.loc[mask, "population"].sum()
            )
            record[f"foreign_born_within_{threshold}m"] = int(
                group.loc[mask, "foreign_born_population"].sum()
            )
            record[f"population_access_pct_{threshold}m"] = (
                record[f"population_within_{threshold}m"]
                / totals["population"]
            )
            record[f"foreign_born_access_pct_{threshold}m"] = (
                record[f"foreign_born_within_{threshold}m"]
                / totals["foreign_born_population"]
            )

        rows.append(record)

    return pd.DataFrame(rows)


def main() -> None:
    raw_feeds = {
        "dart": download_zip(DART_GTFS_URL),
        "trinity": download_zip(TRINITY_GTFS_URL),
    }
    temporal_feeds = {
        prefix: namespace_temporal_feed(content, prefix)
        for prefix, content in raw_feeds.items()
    }

    service_dates = {
        2: select_common_service_date(temporal_feeds, weekday=2),
        5: select_common_service_date(temporal_feeds, weekday=5),
    }
    connections_by_date = {
        service_date: build_active_connections(
            temporal_feeds,
            service_date,
        )
        for service_date in set(service_dates.values())
    }

    transfer_edges = pd.read_csv(
        PROCESSED / "transfer_edges.csv",
        dtype={"from_stop_id": str, "to_stop_id": str},
    )
    transfer_edges["walk_seconds"] = pd.to_numeric(
        transfer_edges["walk_seconds"],
        errors="raise",
    )

    origins = pd.read_csv(
        PROCESSED / "tract_stop_connectors.csv",
        dtype={"geoid": str, "stop_id": str},
    )
    origins["walk_seconds"] = pd.to_numeric(
        origins["walk_seconds"],
        errors="raise",
    )

    provider_connectors = pd.read_csv(
        PROCESSED / "provider_stop_connectors.csv",
        dtype={"provider_id": str, "stop_id": str},
    )
    provider_connectors["walk_seconds"] = pd.to_numeric(
        provider_connectors["walk_seconds"],
        errors="raise",
    )

    providers = pd.read_csv(
        PROCESSED / "provider_locations.csv",
        dtype={"provider_id": str},
    )
    provider_service_map = normalize_provider_service_types(providers)

    tract_points = pd.read_csv(
        PROCESSED / "tract_points_dfw.csv",
        dtype={"geoid": str},
    )
    all_geoids = tract_points["geoid"].astype(str).tolist()

    context = pd.read_csv(
        PROCESSED / "acs_dfw_tracts.csv",
        dtype={"geoid": str},
    )

    access_frames = []
    service_frames = []
    metadata_rows = []

    for scenario in SCENARIOS:
        service_date = service_dates[scenario["weekday"]]
        connections = connections_by_date[service_date]

        reachability = calculate_provider_reachability_matrix(
            connections,
            transfer_edges,
            origins,
            provider_connectors,
            scenario_id=scenario["scenario_id"],
            departure_seconds=scenario["departure_seconds"],
            thresholds=THRESHOLDS,
        )

        access = aggregate_provider_reachability(
            reachability,
            all_geoids,
            scenario_id=scenario["scenario_id"],
            thresholds=THRESHOLDS,
        )
        access["scenario_label"] = scenario["scenario_label"]
        access["departure_time"] = scenario["departure_time"]
        access["service_date"] = service_date.isoformat()
        access_frames.append(access)

        service_access = aggregate_service_type_reachability(
            reachability,
            provider_service_map,
            all_geoids,
            scenario_id=scenario["scenario_id"],
            thresholds=THRESHOLDS,
        )
        service_access["scenario_label"] = scenario["scenario_label"]
        service_access["departure_time"] = scenario["departure_time"]
        service_access["service_date"] = service_date.isoformat()
        service_frames.append(service_access)

        metadata_rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "scenario_label": scenario["scenario_label"],
                "service_date": service_date.isoformat(),
                "departure_time": scenario["departure_time"],
                "weekday_index": scenario["weekday"],
                "active_connections": len(connections),
            }
        )

    access = pd.concat(access_frames, ignore_index=True)
    service_access = pd.concat(service_frames, ignore_index=True)

    access.to_csv(
        PROCESSED / "tract_temporal_accessibility.csv",
        index=False,
    )
    service_access.to_csv(
        PROCESSED / "tract_temporal_service_type_accessibility.csv",
        index=False,
    )
    pd.DataFrame(metadata_rows).to_csv(
        PROCESSED / "temporal_scenario_metadata.csv",
        index=False,
    )

    summary = build_summary(
        access,
        context,
        ["scenario_id", "scenario_label", "departure_time", "service_date"],
    )
    summary.to_csv(
        PROCESSED / "temporal_accessibility_summary.csv",
        index=False,
    )

    service_summary = build_summary(
        service_access,
        context,
        [
            "scenario_id",
            "scenario_label",
            "departure_time",
            "service_date",
            "service_type",
        ],
    )
    service_summary.to_csv(
        PROCESSED / "temporal_service_type_summary.csv",
        index=False,
    )

    print(pd.DataFrame(metadata_rows).to_dict("records"))
    print(summary.to_dict("records"))


if __name__ == "__main__":
    main()
