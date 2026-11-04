from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import pytest

from src.ingestion.gtfs import (
    build_gtfs_summary,
    inspect_gtfs_zip,
    read_gtfs_table,
)


def make_gtfs_zip(include_stop_times=True):
    files = {
        "agency.txt": "agency_id,agency_name,agency_url,agency_timezone\nDART,DART,https://dart.org,America/Chicago\n",
        "stops.txt": "stop_id,stop_name,stop_lat,stop_lon\n1,Main Stop,32.8,-96.8\n",
        "routes.txt": "route_id,route_type\nR1,3\n",
        "trips.txt": "route_id,service_id,trip_id\nR1,WKD,T1\n",
    }
    if include_stop_times:
        files["stop_times.txt"] = (
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
            "T1,08:00:00,08:00:00,1,1\n"
        )

    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_inspect_gtfs_zip_accepts_required_files():
    result = inspect_gtfs_zip(make_gtfs_zip())

    assert result["required_files_present"] is True
    assert "stops.txt" in result["files"]


def test_inspect_gtfs_zip_rejects_missing_required_file():
    with pytest.raises(ValueError, match="stop_times.txt"):
        inspect_gtfs_zip(make_gtfs_zip(include_stop_times=False))


def test_read_gtfs_table():
    frame = read_gtfs_table(make_gtfs_zip(), "stops.txt")

    assert frame.loc[0, "stop_id"] == "1"
    assert frame.loc[0, "stop_name"] == "Main Stop"


def test_build_gtfs_summary_counts_core_records():
    summary = build_gtfs_summary(make_gtfs_zip())

    assert summary == {
        "stops": 1,
        "routes": 1,
        "trips": 1,
        "stop_times": 1,
    }
