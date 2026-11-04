# DART GTFS ingestion

## Source

Dallas Area Rapid Transit publishes a single GTFS Schedule feed covering its fixed-route network. DART states that the feed includes bus, light rail, Trinity Railway Express (TRE), M-Line Trolley, and streetcar service.

Official documentation:

- https://www.dart.org/about/about-dart/fixed-route-schedule
- Latest schedule: https://www.dart.org/transitdata/latest/google_transit.zip

DART notes that schedule files are updated for major service changes and may also be updated for weather or special events. The project therefore treats the feed as a versioned operational input rather than a static reference file.

## Initial ingestion contract

The pipeline requires these GTFS files:

- agency.txt
- stops.txt
- routes.txt
- trips.txt
- stop_times.txt

The following are accepted when present:

- calendar.txt
- calendar_dates.txt
- shapes.txt
- transfers.txt
- feed_info.txt

The first processed layer preserves stops, routes, and trips as normalized CSV files and records feed-level counts for stops, routes, trips, and stop-time rows.

The large stop_times table remains an ingestion input for routing and is not treated as a hand-maintained project dataset.

## Interpretation

GTFS schedule times are scheduled service, not observed travel times. They can differ from actual conditions because of traffic, disruptions, weather, and operational changes.

The accessibility model will therefore describe **scheduled transit accessibility** unless a later phase explicitly incorporates GTFS-Realtime or observed performance data.
