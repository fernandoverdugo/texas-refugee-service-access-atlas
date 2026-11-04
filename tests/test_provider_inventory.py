from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.providers import load_provider_inventory


def test_provider_inventory_loads():
    path = Path("data/processed/provider_inventory.csv")
    frame = load_provider_inventory(path)

    assert len(frame) >= 7
    assert set(frame["county"]) == {"Dallas", "Tarrant"}
    assert frame["provider_id"].is_unique
    assert frame["refugee_specific"].all()


def test_provider_inventory_rejects_duplicate_ids(tmp_path):
    frame = pd.DataFrame(
        {
            "provider_id": ["x", "x"],
            "organization": ["A", "B"],
            "location_name": ["A", "B"],
            "address": ["1 Main St", "2 Main St"],
            "city": ["Dallas", "Dallas"],
            "state": ["TX", "TX"],
            "zip": ["75201", "75201"],
            "county": ["Dallas", "Dallas"],
            "service_categories": ["resettlement", "resettlement"],
            "refugee_specific": [True, True],
            "source_url": ["https://example.com/a", "https://example.com/b"],
            "source_type": ["organization", "organization"],
            "verified_on": ["2026-11-03", "2026-11-03"],
            "notes": ["", ""],
        }
    )
    path = tmp_path / "providers.csv"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="duplicate provider_id"):
        load_provider_inventory(path)
