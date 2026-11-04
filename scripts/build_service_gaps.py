from pathlib import Path

import pandas as pd

from src.analysis.service_gaps import (
    classify_service_gaps,
    context_thresholds,
    rank_priority_tracts,
    summarize_service_gaps,
)


PROCESSED = Path("data/processed")


def main() -> None:
    context = pd.read_csv(
        PROCESSED / "acs_dfw_tracts.csv",
        dtype={"geoid": str},
    )

    overall = pd.read_csv(
        PROCESSED / "tract_temporal_accessibility.csv",
        dtype={"geoid": str},
    )
    overall["service_type"] = "all"
    overall["service_label"] = "All verified services"

    service = pd.read_csv(
        PROCESSED / "tract_temporal_service_type_accessibility.csv",
        dtype={"geoid": str},
    )

    labels = {
        "resettlement_case_management": "Resettlement & case management",
        "employment": "Employment",
        "education": "Education & English-language support",
        "health": "Health & behavioral health",
        "immigration": "Immigration & legal support",
        "cash_benefits": "Cash & benefits assistance",
    }
    service["service_label"] = service["service_type"].map(labels)

    columns = [
        "geoid",
        "scenario_id",
        "scenario_label",
        "departure_time",
        "service_date",
        "service_type",
        "service_label",
        "providers_within_30m",
        "providers_within_45m",
        "providers_within_60m",
    ]

    combined = pd.concat(
        [
            overall[columns],
            service[columns],
        ],
        ignore_index=True,
    )

    thresholds = context_thresholds(context)

    classified = classify_service_gaps(
        combined,
        context,
        thresholds=thresholds,
    )

    classified.to_csv(
        PROCESSED / "tract_service_gap_classification.csv",
        index=False,
    )

    summary = summarize_service_gaps(classified)
    summary = summary.merge(
        combined[
            [
                "scenario_id",
                "service_type",
                "scenario_label",
                "departure_time",
                "service_date",
                "service_label",
            ]
        ].drop_duplicates(),
        on=["scenario_id", "service_type"],
        how="left",
        validate="many_to_one",
    )
    summary.to_csv(
        PROCESSED / "service_gap_summary.csv",
        index=False,
    )

    priority = rank_priority_tracts(classified, top_n=25)
    priority.to_csv(
        PROCESSED / "service_gap_priority_tracts.csv",
        index=False,
    )

    threshold_rows = [
        {
            "indicator": indicator,
            "quantile": 0.75,
            "threshold": threshold,
        }
        for indicator, threshold in thresholds.items()
    ]
    pd.DataFrame(threshold_rows).to_csv(
        PROCESSED / "service_gap_thresholds.csv",
        index=False,
    )

    severe = classified[classified["gap_class"] == "Severe gap"]
    print(
        {
            "rows": len(classified),
            "severe_rows": len(severe),
            "thresholds": thresholds,
        }
    )
    print(
        summary[
            (summary["scenario_id"] == "weekday_midday")
            & (summary["gap_class"].isin(["High gap", "Severe gap"]))
        ].to_dict("records")
    )


if __name__ == "__main__":
    main()
