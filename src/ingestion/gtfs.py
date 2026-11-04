from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd
import requests


DART_GTFS_URL = "https://www.dart.org/transitdata/latest/google_transit.zip"

REQUIRED_GTFS_FILES = {
    "agency.txt",
    "stops.txt",
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
}

OPTIONAL_GTFS_FILES = {
    "calendar.txt",
    "calendar_dates.txt",
    "shapes.txt",
    "transfers.txt",
    "feed_info.txt",
}


def download_gtfs_zip(
    url: str = DART_GTFS_URL,
    timeout: int = 90,
) -> bytes:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "zip" not in content_type and "octet-stream" not in content_type:
        raise RuntimeError(
            f"GTFS endpoint returned unexpected content type: {content_type or 'unknown'}"
        )

    if not response.content:
        raise RuntimeError("GTFS endpoint returned an empty response")

    return response.content


def inspect_gtfs_zip(content: bytes) -> dict[str, object]:
    try:
        with ZipFile(BytesIO(content)) as archive:
            names = set(archive.namelist())
            missing = REQUIRED_GTFS_FILES.difference(names)
            if missing:
                raise ValueError(
                    f"GTFS archive missing required files: {sorted(missing)}"
                )

            return {
                "files": sorted(names),
                "required_files_present": True,
                "optional_files_present": sorted(OPTIONAL_GTFS_FILES.intersection(names)),
            }
    except BadZipFile as exc:
        raise ValueError("GTFS response is not a valid ZIP archive") from exc


def read_gtfs_table(content: bytes, filename: str) -> pd.DataFrame:
    with ZipFile(BytesIO(content)) as archive:
        if filename not in archive.namelist():
            raise ValueError(f"GTFS archive does not contain {filename}")
        with archive.open(filename) as handle:
            return pd.read_csv(handle, dtype=str)


def build_gtfs_summary(content: bytes) -> dict[str, int]:
    inspect_gtfs_zip(content)

    stops = read_gtfs_table(content, "stops.txt")
    routes = read_gtfs_table(content, "routes.txt")
    trips = read_gtfs_table(content, "trips.txt")
    stop_times = read_gtfs_table(content, "stop_times.txt")

    required_columns = {
        "stops.txt": (stops, {"stop_id", "stop_name", "stop_lat", "stop_lon"}),
        "routes.txt": (routes, {"route_id", "route_type"}),
        "trips.txt": (trips, {"route_id", "service_id", "trip_id"}),
        "stop_times.txt": (
            stop_times,
            {"trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"},
        ),
    }

    for filename, (frame, columns) in required_columns.items():
        missing = columns.difference(frame.columns)
        if missing:
            raise ValueError(
                f"{filename} missing required columns: {sorted(missing)}"
            )

    return {
        "stops": len(stops),
        "routes": len(routes),
        "trips": len(trips),
        "stop_times": len(stop_times),
    }


def save_core_gtfs_tables(
    content: bytes,
    output_dir: str | Path,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    filenames = ["stops.txt", "routes.txt", "trips.txt"]
    saved = {}

    for filename in filenames:
        frame = read_gtfs_table(content, filename)
        destination = output / filename.replace(".txt", ".csv")
        frame.to_csv(destination, index=False)
        saved[filename] = destination

    return saved
