from pathlib import Path

import pandas as pd

from src.analysis.network import build_multimodal_graph
from src.optimization.facility_location import (
    candidate_access_times,
    score_candidates,
    select_best_candidate,
)


PROCESSED = Path("data/processed")
THRESHOLD_MINUTES = 45
WEIGHT_COLUMN = "foreign_born_population"


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

    origin_connectors = pd.read_csv(
        PROCESSED / "tract_stop_connectors.csv",
        dtype={"geoid": str, "stop_id": str},
    )
    origin_connectors["walk_seconds"] = pd.to_numeric(
        origin_connectors["walk_seconds"],
        errors="raise",
    )

    tract_points = pd.read_csv(
        PROCESSED / "tract_points_dfw.csv",
        dtype={"geoid": str},
    )
    access = pd.read_csv(
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

    times = candidate_access_times(
        graph,
        origin_connectors=origin_connectors,
        candidate_connectors=candidates,
        cutoff_minutes=THRESHOLD_MINUTES,
    )

    scored = score_candidates(
        times,
        tract_context=context,
        baseline_access=access,
        threshold_minutes=THRESHOLD_MINUTES,
        weight_column=WEIGHT_COLUMN,
    )

    scored = scored.merge(
        tract_points[
            ["geoid", "county_name", "longitude", "latitude"]
        ].rename(columns={"geoid": "candidate_geoid"}),
        on="candidate_geoid",
        how="left",
        validate="one_to_one",
    )

    scored["rank"] = range(1, len(scored) + 1)
    scored.to_csv(
        PROCESSED / "facility_location_candidates.csv",
        index=False,
    )

    best = select_best_candidate(scored)

    total_weight = float(context[WEIGHT_COLUMN].sum())
    baseline_covered = context[
        context["geoid"].isin(
            access.loc[
                access[f"providers_within_{THRESHOLD_MINUTES}m"] > 0,
                "geoid",
            ]
        )
    ][WEIGHT_COLUMN].sum()

    new_covered = float(best["newly_covered_weight"])
    optimized_covered = baseline_covered + new_covered

    summary = pd.DataFrame(
        [
            {
                "threshold_minutes": THRESHOLD_MINUTES,
                "objective": WEIGHT_COLUMN,
                "candidate_geoid": best["candidate_geoid"],
                "county_name": best["county_name"],
                "longitude": best["longitude"],
                "latitude": best["latitude"],
                "newly_covered_foreign_born_population": int(new_covered),
                "newly_covered_population": int(best["newly_covered_population"]),
                "newly_covered_no_vehicle_households": int(
                    best["newly_covered_no_vehicle_households"]
                ),
                "newly_covered_tracts": int(best["newly_covered_tracts"]),
                "baseline_covered_foreign_born_population": int(baseline_covered),
                "optimized_covered_foreign_born_population": int(optimized_covered),
                "total_foreign_born_population": int(total_weight),
                "baseline_coverage_pct": baseline_covered / total_weight,
                "optimized_coverage_pct": optimized_covered / total_weight,
                "coverage_gain_pct_points": (
                    optimized_covered - baseline_covered
                )
                / total_weight,
            }
        ]
    )

    summary.to_csv(
        PROCESSED / "facility_location_summary.csv",
        index=False,
    )

    print(summary.iloc[0].to_dict())


if __name__ == "__main__":
    main()
