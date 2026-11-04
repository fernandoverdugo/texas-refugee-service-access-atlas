from io import BytesIO
from zipfile import ZipFile

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from src.ingestion.geography import build_tract_points, join_acs_to_tracts


def test_build_tract_points_returns_wgs84_coordinates():
    frame = gpd.GeoDataFrame(
        {
            "GEOID": ["48113000100"],
            "STATEFP": ["48"],
            "COUNTYFP": ["113"],
            "TRACTCE": ["000100"],
            "county_name": ["Dallas"],
        },
        geometry=[
            Polygon(
                [
                    (-96.81, 32.77),
                    (-96.80, 32.77),
                    (-96.80, 32.78),
                    (-96.81, 32.78),
                ]
            )
        ],
        crs="EPSG:4326",
    )

    points = build_tract_points(frame)

    assert points.loc[0, "geoid"] == "48113000100"
    assert -97 < points.loc[0, "longitude"] < -96
    assert 32 < points.loc[0, "latitude"] < 33


def test_join_acs_to_tracts_requires_complete_match():
    tracts = gpd.GeoDataFrame(
        {
            "GEOID": ["48113000100"],
            "STATEFP": ["48"],
            "COUNTYFP": ["113"],
            "TRACTCE": ["000100"],
            "county_name": ["Dallas"],
        },
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        crs="EPSG:4326",
    )
    acs = pd.DataFrame(
        {
            "geoid": ["48113000100"],
            "population": [1000],
        }
    )

    result = join_acs_to_tracts(tracts, acs)
    assert result.loc[0, "population"] == 1000
