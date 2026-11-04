from pathlib import Path

import pandas as pd

from src.analysis.network import build_multimodal_graph
from src.analysis.service_accessibility import calculate_service_type_accessibility
from src.analysis.service_types import provider_service_type_strings


PROCESSED = Path("data/processed")


def main() -> None:
    transit_edges = pd.read_csv(PROCESSED / "transit_edges.csv", dtype=str)
    transfer_edges = pd.read_csv(PROCESSED / "transfer_edges.csv", dtype=str)

    transit_edges["travel_seconds"] = pd.to_numeric(
        transit_edges["travel_seconds"],
        errors="raise",
    )
    transfer_edges["walk_seconds"] = pd.to_numeric(
        transfer_edges["walk_seconds"],
        errors="raise",
    )

    graph = build_multimodal_graph(transit_edges, transfer_edges)

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
    tract_points = pd.read_csv(
        PROCESSED / "tract_points_dfw.csv",
        dtype={"geoid": str},
    )

    accessibility = calculate_service_type_accessibility(
        graph,
        origins,
        provider_connectors,
        providers,
        all_geoids=tract_points["geoid"].astype(str).tolist(),
    )

    context = pd.read_csv(
        PROCESSED / "acs_dfw_tracts.csv",
        dtype={"geoid": str},
    )[
        [
            "geoid",
            "county_name",
            "population",
            "foreign_born_population",
            "population_below_poverty",
            "households_no_vehicle",
        ]
    ]

    accessibility = accessibility.merge(
        context,
        on="geoid",
        how="left",
        validate="many_to_one",
    )

    provider_types = provider_service_type_strings(providers)
    provider_types.to_csv(
        PROCESSED / "provider_service_types.csv",
        index=False,
    )
    accessibility.to_csv(
        PROCESSED / "tract_service_type_accessibility.csv",
        index=False,
    )

    summary_source = accessibility.copy()
    summary_source["accessible_45"] = (
        summary_source["service_locations_within_45m"] > 0
    )
    summary_source["foreign_born_45m"] = summary_source[
        "foreign_born_population"
    ].where(summary_source["accessible_45"], 0)

    summary = (
        summary_source.groupby(
            ["service_type", "service_label", "provider_locations"],
            as_index=False,
        )
        .agg(
            tracts_with_45m_access=("accessible_45", "sum"),
            foreign_born_population_with_45m_access=(
                "foreign_born_45m",
                "sum",
            ),
        )
    )

    total_foreign_born = float(context["foreign_born_population"].sum())
    summary["foreign_born_45m_access_pct"] = (
        summary["foreign_born_population_with_45m_access"]
        / total_foreign_born
    )
    summary.to_csv(
        PROCESSED / "service_type_accessibility_summary.csv",
        index=False,
    )

    print(summary.to_dict("records"))


if __name__ == "__main__":
    main()
