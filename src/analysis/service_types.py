from __future__ import annotations

import pandas as pd


SERVICE_TYPE_LABELS = {
    "resettlement_case_management": "Resettlement & case management",
    "employment": "Employment",
    "education": "Education & English-language support",
    "health": "Health & behavioral health",
    "immigration": "Immigration & legal support",
    "cash_benefits": "Cash & benefits assistance",
}

RAW_CATEGORY_MAP = {
    "resettlement": {"resettlement_case_management"},
    "case_management": {"resettlement_case_management"},
    "refugee_services": {"resettlement_case_management"},
    "resource_navigation": {"resettlement_case_management"},
    "family_assistance": {"resettlement_case_management"},
    "employment": {"employment"},
    "education": {"education"},
    "health_support": {"health"},
    "mental_health": {"health"},
    "immigration": {"immigration"},
    "cash_assistance": {"cash_benefits"},
}


def normalize_provider_service_types(
    providers: pd.DataFrame,
) -> pd.DataFrame:
    required = {"provider_id", "service_categories"}
    if missing := required.difference(providers.columns):
        raise ValueError(f"providers missing columns: {sorted(missing)}")

    rows = []

    for record in providers.to_dict("records"):
        raw_categories = [
            value.strip()
            for value in str(record["service_categories"]).split(";")
            if value.strip()
        ]
        normalized = set()

        for category in raw_categories:
            normalized.update(RAW_CATEGORY_MAP.get(category, set()))

        for service_type in sorted(normalized):
            rows.append(
                {
                    "provider_id": record["provider_id"],
                    "service_type": service_type,
                    "service_label": SERVICE_TYPE_LABELS[service_type],
                }
            )

    frame = pd.DataFrame(rows)

    if frame.empty:
        raise ValueError("No provider service categories could be normalized")

    if frame.duplicated(["provider_id", "service_type"]).any():
        raise ValueError("Provider service-type mapping contains duplicates")

    return frame.sort_values(
        ["service_type", "provider_id"]
    ).reset_index(drop=True)


def provider_service_type_strings(
    providers: pd.DataFrame,
) -> pd.DataFrame:
    mapping = normalize_provider_service_types(providers)

    grouped = (
        mapping.groupby("provider_id", as_index=False)
        .agg(
            normalized_service_types=(
                "service_type",
                lambda values: ";".join(sorted(values)),
            ),
            normalized_service_labels=(
                "service_label",
                lambda values: ";".join(sorted(values)),
            ),
        )
    )

    return grouped
