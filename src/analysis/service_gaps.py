from __future__ import annotations

import pandas as pd


GAP_LABELS = {
    0: "Lower gap",
    1: "Moderate gap",
    2: "High gap",
    3: "Severe gap",
}

CONTEXT_COLUMNS = [
    "foreign_born_population",
    "population_below_poverty",
    "households_no_vehicle",
]


def context_thresholds(
    context: pd.DataFrame,
    quantile: float = 0.75,
) -> dict[str, float]:
    missing = set(CONTEXT_COLUMNS).difference(context.columns)
    if missing:
        raise ValueError(f"context missing columns: {sorted(missing)}")

    return {
        column: float(context[column].quantile(quantile))
        for column in CONTEXT_COLUMNS
    }


def add_context_flags(
    context: pd.DataFrame,
    thresholds: dict[str, float],
) -> pd.DataFrame:
    frame = context.copy()

    for column in CONTEXT_COLUMNS:
        if column not in thresholds:
            raise ValueError(f"missing threshold for {column}")
        frame[f"high_{column}"] = frame[column] >= thresholds[column]

    flag_columns = [f"high_{column}" for column in CONTEXT_COLUMNS]
    frame["high_context_indicators"] = frame[flag_columns].sum(axis=1).astype(int)
    frame["elevated_context"] = frame["high_context_indicators"] >= 2

    return frame


def classify_service_gaps(
    access: pd.DataFrame,
    context: pd.DataFrame,
    thresholds: dict[str, float] | None = None,
) -> pd.DataFrame:
    required_access = {
        "geoid",
        "scenario_id",
        "service_type",
        "providers_within_45m",
        "providers_within_60m",
    }
    if missing := required_access.difference(access.columns):
        raise ValueError(f"access missing columns: {sorted(missing)}")

    required_context = {
        "geoid",
        "county_name",
        "population",
        *CONTEXT_COLUMNS,
    }
    if missing := required_context.difference(context.columns):
        raise ValueError(f"context missing columns: {sorted(missing)}")

    threshold_values = thresholds or context_thresholds(context)

    context_frame = add_context_flags(context, threshold_values)
    context_frame["geoid"] = context_frame["geoid"].astype(str).str.zfill(11)

    frame = access.copy()
    frame["geoid"] = frame["geoid"].astype(str).str.zfill(11)
    frame = frame.merge(
        context_frame[
            [
                "geoid",
                "county_name",
                "population",
                *CONTEXT_COLUMNS,
                *[f"high_{column}" for column in CONTEXT_COLUMNS],
                "high_context_indicators",
                "elevated_context",
            ]
        ],
        on="geoid",
        how="left",
        validate="many_to_one",
    )

    within_45 = frame["providers_within_45m"] > 0
    within_60 = frame["providers_within_60m"] > 0

    frame["base_gap_level"] = 0
    frame.loc[~within_45 & within_60, "base_gap_level"] = 1
    frame.loc[~within_60, "base_gap_level"] = 2

    frame["gap_level"] = frame["base_gap_level"] + frame[
        "elevated_context"
    ].astype(int)
    frame["gap_level"] = frame["gap_level"].clip(upper=3).astype(int)
    frame["gap_class"] = frame["gap_level"].map(GAP_LABELS)

    return frame


def summarize_service_gaps(
    classified: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "scenario_id",
        "service_type",
        "gap_class",
        "gap_level",
        "geoid",
        "population",
        "foreign_born_population",
        "population_below_poverty",
        "households_no_vehicle",
    }
    if missing := required.difference(classified.columns):
        raise ValueError(f"classified data missing columns: {sorted(missing)}")

    return (
        classified.groupby(
            ["scenario_id", "service_type", "gap_level", "gap_class"],
            as_index=False,
        )
        .agg(
            tract_count=("geoid", "nunique"),
            population=("population", "sum"),
            foreign_born_population=("foreign_born_population", "sum"),
            population_below_poverty=("population_below_poverty", "sum"),
            households_no_vehicle=("households_no_vehicle", "sum"),
        )
        .sort_values(
            ["scenario_id", "service_type", "gap_level"],
            ascending=[True, True, False],
        )
        .reset_index(drop=True)
    )


def rank_priority_tracts(
    classified: pd.DataFrame,
    top_n: int = 25,
) -> pd.DataFrame:
    frame = classified.copy()

    frame = frame.sort_values(
        [
            "scenario_id",
            "service_type",
            "gap_level",
            "high_context_indicators",
            "foreign_born_population",
            "households_no_vehicle",
            "population_below_poverty",
            "geoid",
        ],
        ascending=[True, True, False, False, False, False, False, True],
    )

    frame["priority_rank"] = (
        frame.groupby(["scenario_id", "service_type"]).cumcount() + 1
    )

    return frame[frame["priority_rank"] <= top_n].reset_index(drop=True)
