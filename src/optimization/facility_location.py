from __future__ import annotations

import networkx as nx
import pandas as pd


def normalize_geoid(value: object) -> str:
    text = str(value)
    return text.zfill(11) if text.isdigit() else text


def candidate_access_times(
    graph: nx.DiGraph,
    origin_connectors: pd.DataFrame,
    candidate_connectors: pd.DataFrame,
    cutoff_minutes: int = 45,
) -> pd.DataFrame:
    required_origins = {"geoid", "stop_id", "walk_seconds"}
    required_candidates = {"geoid", "stop_id", "walk_seconds"}

    if missing := required_origins.difference(origin_connectors.columns):
        raise ValueError(f"origin connectors missing columns: {sorted(missing)}")
    if missing := required_candidates.difference(candidate_connectors.columns):
        raise ValueError(f"candidate connectors missing columns: {sorted(missing)}")

    reverse = graph.reverse(copy=False)
    origins_by_stop: dict[str, list[tuple[str, float]]] = {}
    for row in origin_connectors.itertuples(index=False):
        origins_by_stop.setdefault(row.stop_id, []).append(
            (str(row.geoid), float(row.walk_seconds))
        )

    rows = []
    cutoff_seconds = cutoff_minutes * 60

    for candidate_geoid, group in candidate_connectors.groupby("geoid"):
        best: dict[str, float] = {}

        for connector in group.itertuples(index=False):
            if connector.stop_id not in reverse:
                continue

            lengths = nx.single_source_dijkstra_path_length(
                reverse,
                connector.stop_id,
                weight="weight",
                cutoff=cutoff_seconds,
            )
            destination_walk = float(connector.walk_seconds)

            for origin_stop, network_seconds in lengths.items():
                for origin_geoid, origin_walk in origins_by_stop.get(origin_stop, []):
                    total = origin_walk + float(network_seconds) + destination_walk
                    if total > cutoff_seconds:
                        continue
                    previous = best.get(origin_geoid)
                    if previous is None or total < previous:
                        best[origin_geoid] = total

        for origin_geoid, seconds in best.items():
            rows.append(
                {
                    "candidate_geoid": str(candidate_geoid),
                    "origin_geoid": str(origin_geoid),
                    "travel_minutes": seconds / 60,
                }
            )

    return pd.DataFrame(rows)


def score_candidates(
    access_times: pd.DataFrame,
    tract_context: pd.DataFrame,
    baseline_access: pd.DataFrame,
    threshold_minutes: int = 45,
    weight_column: str = "foreign_born_population",
) -> pd.DataFrame:
    required_context = {
        "geoid",
        weight_column,
        "population",
        "foreign_born_population",
        "population_below_poverty",
        "households_no_vehicle",
    }
    required_baseline = {"geoid", f"providers_within_{threshold_minutes}m"}

    if missing := required_context.difference(tract_context.columns):
        raise ValueError(f"tract context missing columns: {sorted(missing)}")
    if missing := required_baseline.difference(baseline_access.columns):
        raise ValueError(f"baseline access missing columns: {sorted(missing)}")

    context = tract_context.copy()
    context["geoid"] = context["geoid"].map(normalize_geoid)

    baseline = baseline_access.copy()
    baseline["geoid"] = baseline["geoid"].map(normalize_geoid)

    access_times = access_times.copy()
    access_times["origin_geoid"] = access_times["origin_geoid"].map(normalize_geoid)
    access_times["candidate_geoid"] = access_times["candidate_geoid"].map(normalize_geoid)
    baseline_flag = baseline.set_index("geoid")[
        f"providers_within_{threshold_minutes}m"
    ].gt(0)

    underserved = context[
        ~context["geoid"].map(baseline_flag).fillna(False)
    ].copy()

    if access_times.empty:
        return pd.DataFrame(
            columns=[
                "candidate_geoid",
                "newly_covered_weight",
                "newly_covered_population",
                "newly_covered_no_vehicle_households",
                "newly_covered_tracts",
            ]
        )

    access = access_times.merge(
        underserved[
            [
                "geoid",
                weight_column,
                "population",
                "foreign_born_population",
                "population_below_poverty",
                "households_no_vehicle",
            ]
        ],
        left_on="origin_geoid",
        right_on="geoid",
        how="inner",
    )

    scored = (
        access.groupby("candidate_geoid", as_index=False)
        .agg(
            newly_covered_weight=(weight_column, "sum"),
            newly_covered_population=("population", "sum"),
            newly_covered_foreign_born_population=("foreign_born_population", "sum"),
            newly_covered_population_below_poverty=("population_below_poverty", "sum"),
            newly_covered_no_vehicle_households=("households_no_vehicle", "sum"),
            newly_covered_tracts=("origin_geoid", "nunique"),
        )
        .sort_values(
            [
                "newly_covered_weight",
                "newly_covered_no_vehicle_households",
                "newly_covered_population",
                "candidate_geoid",
            ],
            ascending=[False, False, False, True],
        )
        .reset_index(drop=True)
    )

    return scored


def select_best_candidate(
    scored: pd.DataFrame,
) -> pd.Series:
    if scored.empty:
        raise ValueError("No candidate sites produced positive modeled coverage")
    return scored.iloc[0]



def summarize_objective_scenario(
    scored: pd.DataFrame,
    tract_context: pd.DataFrame,
    baseline_access: pd.DataFrame,
    tract_points: pd.DataFrame,
    objective: str,
    threshold_minutes: int = 45,
) -> dict[str, object]:
    best = select_best_candidate(scored)

    context = tract_context.copy()
    context["geoid"] = context["geoid"].map(normalize_geoid)

    baseline = baseline_access.copy()
    baseline["geoid"] = baseline["geoid"].map(normalize_geoid)

    total_objective = float(context[objective].sum())
    covered_geoids = set(
        baseline.loc[
            baseline[f"providers_within_{threshold_minutes}m"] > 0,
            "geoid",
        ]
    )
    baseline_covered = float(
        context.loc[context["geoid"].isin(covered_geoids), objective].sum()
    )
    optimized_covered = baseline_covered + float(best["newly_covered_weight"])

    points = tract_points.copy()
    points["geoid"] = points["geoid"].map(normalize_geoid)
    point = points.loc[points["geoid"] == normalize_geoid(best["candidate_geoid"])].iloc[0]

    return {
        "threshold_minutes": threshold_minutes,
        "objective": objective,
        "candidate_geoid": normalize_geoid(best["candidate_geoid"]),
        "county_name": point["county_name"],
        "longitude": float(point["longitude"]),
        "latitude": float(point["latitude"]),
        "newly_covered_objective": int(best["newly_covered_weight"]),
        "newly_covered_population": int(best["newly_covered_population"]),
        "newly_covered_foreign_born_population": int(
            best["newly_covered_foreign_born_population"]
        ),
        "newly_covered_population_below_poverty": int(
            best["newly_covered_population_below_poverty"]
        ),
        "newly_covered_no_vehicle_households": int(
            best["newly_covered_no_vehicle_households"]
        ),
        "newly_covered_tracts": int(best["newly_covered_tracts"]),
        "baseline_covered_objective": int(baseline_covered),
        "optimized_covered_objective": int(optimized_covered),
        "total_objective": int(total_objective),
        "baseline_coverage_pct": baseline_covered / total_objective
        if total_objective
        else 0.0,
        "optimized_coverage_pct": optimized_covered / total_objective
        if total_objective
        else 0.0,
        "coverage_gain_pct_points": (
            (optimized_covered - baseline_covered) / total_objective
            if total_objective
            else 0.0
        ),
    }
