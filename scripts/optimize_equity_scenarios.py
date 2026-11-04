from pathlib import Path

import pandas as pd

from src.analysis.network import build_multimodal_graph
from src.optimization.facility_location import (
    candidate_access_times,
    score_candidates,
    summarize_objective_scenario,
)


PROCESSED = Path("data/processed")
THRESHOLD_MINUTES = 45

OBJECTIVES = {
    "foreign_born_population": "Foreign-born population",
    "population": "Total population",
    "households_no_vehicle": "No-vehicle households",
    "population_below_poverty": "Population below poverty",
}


def main() -> None:
    transit_edges = pd.read_csv(PROCESSED / "transit_edges.csv", dtype=str)
    transfer_edges = pd.read_csv(PROCESSED / "transfer_edges.csv", dtype=str)

    transit_edges["travel_seconds"] = pd.to_numeric(
        transit_edges["travel_seconds"], errors="raise"
    )
    transfer_edges["walk_seconds"] = pd.to_numeric(
        transfer_edges["walk_seconds"], errors="raise"
    )

    graph = build_multimodal_graph(transit_edges, transfer_edges)

    origin_connectors = pd.read_csv(
        PROCESSED / "tract_stop_connectors.csv",
        dtype={"geoid": str, "stop_id": str},
    )
    origin_connectors["walk_seconds"] = pd.to_numeric(
        origin_connectors["walk_seconds"], errors="raise"
    )

    tract_points = pd.read_csv(
        PROCESSED / "tract_points_dfw.csv",
        dtype={"geoid": str},
    )
    baseline = pd.read_csv(
        PROCESSED / "tract_service_accessibility.csv",
        dtype={"geoid": str},
    )
    context = pd.read_csv(
        PROCESSED / "acs_dfw_tracts.csv",
        dtype={"geoid": str},
    )

    candidates = origin_connectors[
        origin_connectors["geoid"].isin(tract_points["geoid"])
    ].copy()

    access_times = candidate_access_times(
        graph,
        origin_connectors=origin_connectors,
        candidate_connectors=candidates,
        cutoff_minutes=THRESHOLD_MINUTES,
    )

    scenario_rows = []
    candidate_rows = []

    for objective, label in OBJECTIVES.items():
        scored = score_candidates(
            access_times,
            tract_context=context,
            baseline_access=baseline,
            threshold_minutes=THRESHOLD_MINUTES,
            weight_column=objective,
        ).copy()

        scored["scenario_id"] = objective
        scored["scenario_label"] = label
        scored["rank"] = range(1, len(scored) + 1)

        candidate_rows.append(
            scored.head(25)
        )

        summary = summarize_objective_scenario(
            scored=scored,
            tract_context=context,
            baseline_access=baseline,
            tract_points=tract_points,
            objective=objective,
            threshold_minutes=THRESHOLD_MINUTES,
        )
        summary["scenario_id"] = objective
        summary["scenario_label"] = label
        scenario_rows.append(summary)

    pd.DataFrame(scenario_rows).to_csv(
        PROCESSED / "facility_location_scenarios.csv",
        index=False,
    )

    pd.concat(candidate_rows, ignore_index=True).to_csv(
        PROCESSED / "facility_location_scenario_candidates.csv",
        index=False,
    )

    print(pd.DataFrame(scenario_rows).to_dict("records"))


if __name__ == "__main__":
    main()
