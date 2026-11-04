import pandas as pd

from src.analysis.service_types import (
    normalize_provider_service_types,
    provider_service_type_strings,
)


def test_normalize_provider_service_types_maps_raw_categories():
    providers = pd.DataFrame(
        {
            "provider_id": ["p1"],
            "service_categories": [
                "resettlement;case_management;employment;health_support;immigration"
            ],
        }
    )

    result = normalize_provider_service_types(providers)

    assert set(result["service_type"]) == {
        "resettlement_case_management",
        "employment",
        "health",
        "immigration",
    }


def test_provider_service_type_strings_are_unique_and_sorted():
    providers = pd.DataFrame(
        {
            "provider_id": ["p1"],
            "service_categories": [
                "education;employment;education"
            ],
        }
    )

    result = provider_service_type_strings(providers)

    assert result.loc[0, "normalized_service_types"] == "education;employment"
