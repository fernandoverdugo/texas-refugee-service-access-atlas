from __future__ import annotations

import math

import geopandas as gpd
import networkx as nx
import pandas as pd


EARTH_RADIUS_KM = 6371.0088
DEFAULT_WALK_KPH = 4.8


def gtfs_time_to_seconds(value: str) -> int:
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def build_scheduled_transit_edges(
    stop_times: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
    }
    missing = required.difference(stop_times.columns)
    if missing:
        raise ValueError(f"stop_times missing columns: {sorted(missing)}")

    frame = stop_times.copy()
    frame["stop_sequence"] = pd.to_numeric(frame["stop_sequence"], errors="raise")
    frame = frame.sort_values(["trip_id", "stop_sequence"])

    frame["next_stop_id"] = frame.groupby("trip_id")["stop_id"].shift(-1)
    frame["next_arrival_time"] = frame.groupby("trip_id")["arrival_time"].shift(-1)

    frame = frame.dropna(subset=["next_stop_id", "next_arrival_time"]).copy()
    frame["departure_seconds"] = frame["departure_time"].map(gtfs_time_to_seconds)
    frame["next_arrival_seconds"] = frame["next_arrival_time"].map(gtfs_time_to_seconds)
    frame["travel_seconds"] = (
        frame["next_arrival_seconds"] - frame["departure_seconds"]
    )

    frame = frame[frame["travel_seconds"] >= 0].copy()

    edges = (
        frame.groupby(["stop_id", "next_stop_id"], as_index=False)
        .agg(
            travel_seconds=("travel_seconds", "median"),
            trip_observations=("trip_id", "nunique"),
        )
        .rename(columns={"stop_id": "from_stop_id", "next_stop_id": "to_stop_id"})
    )

    edges["travel_seconds"] = edges["travel_seconds"].round().astype(int)
    return edges


def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def nearest_stops(
    locations: pd.DataFrame,
    stops: pd.DataFrame,
    id_column: str,
    max_walk_km: float = 1.0,
    max_stops: int = 3,
    walk_kph: float = DEFAULT_WALK_KPH,
) -> pd.DataFrame:
    required_locations = {id_column, "latitude", "longitude"}
    required_stops = {"stop_id", "stop_lat", "stop_lon"}

    if missing := required_locations.difference(locations.columns):
        raise ValueError(f"locations missing columns: {sorted(missing)}")
    if missing := required_stops.difference(stops.columns):
        raise ValueError(f"stops missing columns: {sorted(missing)}")

    stop_records = stops.copy()
    stop_records["stop_lat"] = pd.to_numeric(stop_records["stop_lat"], errors="raise")
    stop_records["stop_lon"] = pd.to_numeric(stop_records["stop_lon"], errors="raise")

    rows = []
    for location in locations.to_dict("records"):
        candidates = []
        for stop in stop_records.to_dict("records"):
            distance = haversine_km(
                float(location["latitude"]),
                float(location["longitude"]),
                float(stop["stop_lat"]),
                float(stop["stop_lon"]),
            )
            if distance <= max_walk_km:
                candidates.append((distance, stop["stop_id"]))

        for distance, stop_id in sorted(candidates)[:max_stops]:
            rows.append(
                {
                    id_column: location[id_column],
                    "stop_id": stop_id,
                    "walk_km": distance,
                    "walk_seconds": round(distance / walk_kph * 3600),
                }
            )

    return pd.DataFrame(rows)


def build_graph(transit_edges: pd.DataFrame) -> nx.DiGraph:
    graph = nx.DiGraph()

    for row in transit_edges.itertuples(index=False):
        weight = float(row.travel_seconds)
        existing = graph.get_edge_data(row.from_stop_id, row.to_stop_id)
        if existing is None or weight < existing["weight"]:
            graph.add_edge(
                row.from_stop_id,
                row.to_stop_id,
                weight=weight,
                edge_type="transit",
            )

    return graph



def build_walking_transfer_edges(
    stops: pd.DataFrame,
    max_walk_km: float = 0.30,
    walk_kph: float = DEFAULT_WALK_KPH,
) -> pd.DataFrame:
    required = {"stop_id", "stop_lat", "stop_lon"}
    if missing := required.difference(stops.columns):
        raise ValueError(f"stops missing columns: {sorted(missing)}")

    frame = stops.copy()
    frame["stop_lat"] = pd.to_numeric(frame["stop_lat"], errors="raise")
    frame["stop_lon"] = pd.to_numeric(frame["stop_lon"], errors="raise")

    points = gpd.GeoDataFrame(
        frame[["stop_id"]].copy(),
        geometry=gpd.points_from_xy(frame["stop_lon"], frame["stop_lat"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:32614")

    left = points.copy()
    left["geometry"] = left.geometry.buffer(max_walk_km * 1000)

    pairs = gpd.sjoin(
        left,
        points.rename(columns={"stop_id": "to_stop_id"}),
        how="inner",
        predicate="intersects",
    )
    pairs = pairs.rename(columns={"stop_id": "from_stop_id"})
    pairs = pairs[pairs["from_stop_id"] != pairs["to_stop_id"]].copy()

    point_lookup = points.set_index("stop_id").geometry
    pairs["walk_meters"] = pairs.apply(
        lambda row: point_lookup[row["from_stop_id"]].distance(
            point_lookup[row["to_stop_id"]]
        ),
        axis=1,
    )
    pairs["walk_seconds"] = (
        pairs["walk_meters"] / 1000 / walk_kph * 3600
    ).round().astype(int)

    return pairs[
        ["from_stop_id", "to_stop_id", "walk_meters", "walk_seconds"]
    ].drop_duplicates(["from_stop_id", "to_stop_id"]).reset_index(drop=True)


def build_multimodal_graph(
    transit_edges: pd.DataFrame,
    transfer_edges: pd.DataFrame | None = None,
) -> nx.DiGraph:
    graph = build_graph(transit_edges)

    if transfer_edges is not None:
        for row in transfer_edges.itertuples(index=False):
            weight = float(row.walk_seconds)
            existing = graph.get_edge_data(row.from_stop_id, row.to_stop_id)
            if existing is None or weight < existing["weight"]:
                graph.add_edge(
                    row.from_stop_id,
                    row.to_stop_id,
                    weight=weight,
                    edge_type="walking_transfer",
                )

    return graph
