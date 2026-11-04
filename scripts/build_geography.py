from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.ingestion.geography import (
    build_tract_points,
    download_texas_tracts,
    join_acs_to_tracts,
    load_study_tract_geometries,
)


ACS_PATH = Path("data/processed/acs_dfw_tracts.csv")
TRACTS_PATH = Path("data/processed/tracts_dfw.geojson")
POINTS_PATH = Path("data/processed/tract_points_dfw.csv")


def main() -> None:
    content = download_texas_tracts()
    tracts = load_study_tract_geometries(content)

    acs = pd.read_csv(ACS_PATH, dtype={"geoid": str})
    merged = join_acs_to_tracts(tracts, acs)
    points = build_tract_points(tracts)

    merged.to_file(TRACTS_PATH, driver="GeoJSON")
    points.drop(columns="geometry").to_csv(POINTS_PATH, index=False)

    print(
        {
            "tracts": len(merged),
            "dallas": int((merged["county_name_x"] == "Dallas").sum())
            if "county_name_x" in merged.columns
            else int((merged["county_name"] == "Dallas").sum()),
            "tarrant": int((merged["county_name_x"] == "Tarrant").sum())
            if "county_name_x" in merged.columns
            else int((merged["county_name"] == "Tarrant").sum()),
        }
    )


if __name__ == "__main__":
    main()
