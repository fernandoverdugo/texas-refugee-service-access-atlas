from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import requests

from src.analysis.network import build_scheduled_transit_edges


TRINITY_GTFS_URL = "https://gtfsdata.ridetm.org/gtfs/fwtatransitdata.zip"


def download_zip(url: str, timeout: int = 120) -> bytes:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    if not response.content:
        raise RuntimeError(f"GTFS endpoint returned no content: {url}")
    return response.content


def read_table(content: bytes, filename: str) -> pd.DataFrame:
    with ZipFile(BytesIO(content)) as archive:
        if filename not in archive.namelist():
            raise ValueError(f"GTFS archive missing {filename}")
        with archive.open(filename) as handle:
            return pd.read_csv(handle, dtype=str)


def namespace_feed(
    content: bytes,
    prefix: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    stops = read_table(content, "stops.txt")
    stop_times = read_table(content, "stop_times.txt")

    required_stops = {"stop_id", "stop_name", "stop_lat", "stop_lon"}
    required_times = {
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
    }

    if missing := required_stops.difference(stops.columns):
        raise ValueError(f"stops.txt missing columns: {sorted(missing)}")
    if missing := required_times.difference(stop_times.columns):
        raise ValueError(f"stop_times.txt missing columns: {sorted(missing)}")

    stops = stops.copy()
    stop_times = stop_times.copy()

    stops["source_agency"] = prefix
    stops["source_stop_id"] = stops["stop_id"]
    stops["stop_id"] = prefix + ":" + stops["stop_id"].astype(str)

    stop_times["trip_id"] = prefix + ":" + stop_times["trip_id"].astype(str)
    stop_times["stop_id"] = prefix + ":" + stop_times["stop_id"].astype(str)

    return stops, stop_times


def build_combined_transit_layer(
    feeds: dict[str, bytes],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    stop_frames = []
    edge_frames = []

    for prefix, content in feeds.items():
        stops, stop_times = namespace_feed(content, prefix)
        edges = build_scheduled_transit_edges(stop_times)
        edges["source_agency"] = prefix
        stop_frames.append(stops)
        edge_frames.append(edges)

    combined_stops = pd.concat(stop_frames, ignore_index=True)
    combined_edges = pd.concat(edge_frames, ignore_index=True)

    if combined_stops["stop_id"].duplicated().any():
        raise ValueError("Namespaced combined stops still contain duplicate stop IDs")

    return combined_stops, combined_edges
