from io import BytesIO
from zipfile import ZipFile

from src.ingestion.multimodal_gtfs import namespace_feed


def make_feed():
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon\n1,Stop,32.8,-96.8\n",
        )
        archive.writestr(
            "stop_times.txt",
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
            "T1,08:00:00,08:00:00,1,1\n",
        )
    return buffer.getvalue()


def test_namespace_feed_prevents_cross_agency_id_collisions():
    stops, times = namespace_feed(make_feed(), "dart")

    assert stops.loc[0, "stop_id"] == "dart:1"
    assert stops.loc[0, "source_stop_id"] == "1"
    assert times.loc[0, "trip_id"] == "dart:T1"
    assert times.loc[0, "stop_id"] == "dart:1"
