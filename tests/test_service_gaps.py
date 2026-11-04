import pandas as pd

from src.analysis.service_gaps import (
    add_context_flags,
    classify_service_gaps,
    context_thresholds,
    rank_priority_tracts,
)


def make_context():
    return pd.DataFrame(
        {
            "geoid": ["1", "2", "3", "4"],
            "county_name": ["Dallas"] * 4,
            "population": [100, 100, 100, 100],
            "foreign_born_population": [10, 20, 30, 100],
            "population_below_poverty": [5, 10, 20, 100],
            "households_no_vehicle": [1, 2, 3, 100],
        }
    )


def test_context_flags_use_explicit_thresholds():
    context = make_context()
    thresholds = {
        "foreign_born_population": 50,
        "population_below_poverty": 50,
        "households_no_vehicle": 50,
    }

    result = add_context_flags(context, thresholds)

    assert result.loc[0, "high_context_indicators"] == 0
    assert result.loc[3, "high_context_indicators"] == 3
    assert bool(result.loc[3, "elevated_context"]) is True


def test_gap_classification_elevates_high_context_tract():
    context = make_context()
    access = pd.DataFrame(
        {
            "geoid": ["1", "4"],
            "scenario_id": ["weekday_midday", "weekday_midday"],
            "service_type": ["immigration", "immigration"],
            "providers_within_45m": [0, 0],
            "providers_within_60m": [1, 0],
        }
    )
    thresholds = {
        "foreign_born_population": 50,
        "population_below_poverty": 50,
        "households_no_vehicle": 50,
    }

    result = classify_service_gaps(access, context, thresholds)
    by_geoid = result.set_index("geoid")

    assert by_geoid.loc["00000000001", "gap_class"] == "Moderate gap"
    assert by_geoid.loc["00000000004", "gap_class"] == "Severe gap"


def test_within_45_can_be_elevated_to_moderate():
    context = make_context()
    access = pd.DataFrame(
        {
            "geoid": ["4"],
            "scenario_id": ["weekday_midday"],
            "service_type": ["employment"],
            "providers_within_45m": [1],
            "providers_within_60m": [1],
        }
    )
    thresholds = {
        "foreign_born_population": 50,
        "population_below_poverty": 50,
        "households_no_vehicle": 50,
    }

    result = classify_service_gaps(access, context, thresholds)

    assert result.loc[0, "base_gap_level"] == 0
    assert result.loc[0, "gap_class"] == "Moderate gap"


def test_rank_priority_tracts_orders_severe_before_high():
    frame = pd.DataFrame(
        {
            "scenario_id": ["x", "x"],
            "service_type": ["health", "health"],
            "gap_level": [2, 3],
            "high_context_indicators": [3, 2],
            "foreign_born_population": [1000, 100],
            "households_no_vehicle": [100, 10],
            "population_below_poverty": [200, 20],
            "geoid": ["1", "2"],
        }
    )

    result = rank_priority_tracts(frame, top_n=2)

    assert result.iloc[0]["geoid"] == "2"
    assert result.iloc[0]["priority_rank"] == 1


def test_context_thresholds_returns_quantiles():
    thresholds = context_thresholds(make_context())

    assert set(thresholds) == {
        "foreign_born_population",
        "population_below_poverty",
        "households_no_vehicle",
    }
    assert all(value > 0 for value in thresholds.values())
