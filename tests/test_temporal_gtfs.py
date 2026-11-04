from datetime import date
from io import BytesIO
from zipfile import ZipFile

from src.ingestion.temporal_gtfs import (
    active_service_ids,
    build_active_connections,
    namespace_temporal_feed,
)


def make_temporal_feed():
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "trips.txt",
            "route_id,service_id,trip_id\nR1,WK,T1\nR1,SAT,T2\n",
        )
        archive.writestr(
            "stop_times.txt",
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
            "T1,08:00:00,08:00:00,A,1\n"
            "T1,08:12:00,08:12:00,B,2\n"
            "T2,13:00:00,13:00:00,A,1\n"
            "T2,13:15:00,13:15:00,B,2\n",
        )
        archive.writestr(
            "calendar.txt",
            "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
            "WK,1,1,1,1,1,0,0,20261101,20261130\n"
            "SAT,0,0,0,0,0,1,0,20261101,20261130\n",
        )
        archive.writestr(
            "calendar_dates.txt",
            "service_id,date,exception_type\n"
            "WK,20261104,2\n"
            "SAT,20261104,1\n",
        )
    return buffer.getvalue()


def test_active_service_ids_applies_calendar_date_exceptions():
    tables = namespace_temporal_feed(make_temporal_feed(), "x")

    active = active_service_ids(tables, date(2026, 11, 4))

    assert active == {"x:SAT"}


def test_build_active_connections_filters_by_service_date():
    tables = namespace_temporal_feed(make_temporal_feed(), "x")
    connections = build_active_connections(
        {"x": tables},
        date(2026, 11, 7),
    )

    assert len(connections) == 1
    assert connections.loc[0, "trip_id"] == "x:T2"
    assert connections.loc[0, "from_stop_id"] == "x:A"
    assert connections.loc[0, "to_stop_id"] == "x:B"
    assert connections.loc[0, "departure_seconds"] == 13 * 3600
