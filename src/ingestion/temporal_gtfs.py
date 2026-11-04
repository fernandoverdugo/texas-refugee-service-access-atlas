from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd

from src.analysis.network import gtfs_time_to_seconds
from src.ingestion.multimodal_gtfs import read_table


WEEKDAY_COLUMNS = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}


def namespace_temporal_feed(
    content: bytes,
    prefix: str,
) -> dict[str, pd.DataFrame]:
    trips = read_table(content, "trips.txt").copy()
    stop_times = read_table(content, "stop_times.txt").copy()

    try:
        calendar = read_table(content, "calendar.txt").copy()
    except ValueError:
        calendar = pd.DataFrame()

    try:
        calendar_dates = read_table(content, "calendar_dates.txt").copy()
    except ValueError:
        calendar_dates = pd.DataFrame()

    trips["trip_id"] = prefix + ":" + trips["trip_id"].astype(str)
    trips["service_id"] = prefix + ":" + trips["service_id"].astype(str)

    stop_times["trip_id"] = prefix + ":" + stop_times["trip_id"].astype(str)
    stop_times["stop_id"] = prefix + ":" + stop_times["stop_id"].astype(str)

    if not calendar.empty:
        calendar["service_id"] = prefix + ":" + calendar["service_id"].astype(str)

    if not calendar_dates.empty:
        calendar_dates["service_id"] = (
            prefix + ":" + calendar_dates["service_id"].astype(str)
        )

    return {
        "trips": trips,
        "stop_times": stop_times,
        "calendar": calendar,
        "calendar_dates": calendar_dates,
    }


def parse_gtfs_date(value: str) -> date:
    return datetime.strptime(str(value), "%Y%m%d").date()


def feed_date_bounds(tables: dict[str, pd.DataFrame]) -> tuple[date, date]:
    dates = []

    calendar = tables["calendar"]
    if not calendar.empty:
        dates.extend(calendar["start_date"].map(parse_gtfs_date).tolist())
        dates.extend(calendar["end_date"].map(parse_gtfs_date).tolist())

    calendar_dates = tables["calendar_dates"]
    if not calendar_dates.empty:
        dates.extend(calendar_dates["date"].map(parse_gtfs_date).tolist())

    if not dates:
        raise ValueError("GTFS feed does not define service dates")

    return min(dates), max(dates)


def active_service_ids(
    tables: dict[str, pd.DataFrame],
    service_date: date,
) -> set[str]:
    calendar = tables["calendar"]
    calendar_dates = tables["calendar_dates"]
    active: set[str] = set()

    if not calendar.empty:
        day_column = WEEKDAY_COLUMNS[service_date.weekday()]
        frame = calendar.copy()
        frame["start"] = frame["start_date"].map(parse_gtfs_date)
        frame["end"] = frame["end_date"].map(parse_gtfs_date)
        frame[day_column] = pd.to_numeric(frame[day_column], errors="raise")

        mask = (
            (frame["start"] <= service_date)
            & (frame["end"] >= service_date)
            & (frame[day_column] == 1)
        )
        active.update(frame.loc[mask, "service_id"].astype(str))

    if not calendar_dates.empty:
        exceptions = calendar_dates[
            calendar_dates["date"].map(parse_gtfs_date) == service_date
        ]
        for row in exceptions.itertuples(index=False):
            exception_type = int(row.exception_type)
            if exception_type == 1:
                active.add(str(row.service_id))
            elif exception_type == 2:
                active.discard(str(row.service_id))

    return active


def select_common_service_date(
    feeds: dict[str, dict[str, pd.DataFrame]],
    weekday: int,
    max_lookback_days: int = 180,
) -> date:
    bounds = [feed_date_bounds(tables) for tables in feeds.values()]
    start = max(bound[0] for bound in bounds)
    end = min(bound[1] for bound in bounds)

    if start > end:
        raise ValueError("GTFS feeds do not have overlapping service-date coverage")

    candidate = end
    checked = 0

    while candidate >= start and checked <= max_lookback_days:
        if candidate.weekday() == weekday:
            if all(active_service_ids(tables, candidate) for tables in feeds.values()):
                return candidate
        candidate -= timedelta(days=1)
        checked += 1

    raise ValueError(
        f"No common active service date found for weekday index {weekday}"
    )


def build_active_connections(
    feeds: dict[str, dict[str, pd.DataFrame]],
    service_date: date,
) -> pd.DataFrame:
    frames = []

    for prefix, tables in feeds.items():
        active = active_service_ids(tables, service_date)
        trips = tables["trips"]
        trip_ids = set(
            trips.loc[trips["service_id"].isin(active), "trip_id"].astype(str)
        )

        stop_times = tables["stop_times"]
        frame = stop_times[stop_times["trip_id"].isin(trip_ids)].copy()
        if frame.empty:
            continue

        frame["stop_sequence"] = pd.to_numeric(
            frame["stop_sequence"],
            errors="raise",
        )
        frame = frame.sort_values(["trip_id", "stop_sequence"])
        frame["to_stop_id"] = frame.groupby("trip_id")["stop_id"].shift(-1)
        frame["next_arrival_time"] = frame.groupby("trip_id")[
            "arrival_time"
        ].shift(-1)

        frame = frame.dropna(
            subset=["to_stop_id", "departure_time", "next_arrival_time"]
        ).copy()

        frame["departure_seconds"] = frame["departure_time"].map(
            gtfs_time_to_seconds
        )
        frame["arrival_seconds"] = frame["next_arrival_time"].map(
            gtfs_time_to_seconds
        )
        frame = frame[
            frame["arrival_seconds"] >= frame["departure_seconds"]
        ].copy()
        frame["source_agency"] = prefix

        frames.append(
            frame[
                [
                    "trip_id",
                    "stop_id",
                    "to_stop_id",
                    "departure_seconds",
                    "arrival_seconds",
                    "source_agency",
                ]
            ].rename(columns={"stop_id": "from_stop_id"})
        )

    if not frames:
        raise ValueError(f"No active GTFS connections for {service_date}")

    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(
            ["arrival_seconds", "departure_seconds"],
            ascending=[False, False],
        )
        .reset_index(drop=True)
    )
