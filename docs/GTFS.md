# DFW GTFS ingestion

The transit layer combines official schedule feeds from Dallas Area Rapid Transit (DART) and Trinity Metro.

A two-agency network is necessary because the study area spans Dallas and Tarrant Counties. Using DART alone would systematically understate scheduled transit access in Tarrant County.

## Sources

### Dallas Area Rapid Transit

DART publishes a GTFS Schedule feed covering its fixed-route network.

- Documentation: https://www.dart.org/about/about-dart/fixed-route-schedule
- Current feed: https://www.dart.org/transitdata/latest/google_transit.zip

DART notes that schedule files are updated for major service changes and may also change for weather or special events.

### Trinity Metro

- Current feed: https://gtfsdata.ridetm.org/gtfs/fwtatransitdata.zip

Trinity Metro data are treated as a versioned operational input and may change without notice.

## Required GTFS entities

The ingestion and routing layers use the core GTFS entities required for scheduled routing:

- `agency.txt`
- `stops.txt`
- `routes.txt`
- `trips.txt`
- `stop_times.txt`

Calendar-aware routing additionally uses:

- `calendar.txt`
- `calendar_dates.txt`

Other standard GTFS files are accepted when present.

## Validation

The ingestion layer validates:

- required files
- required columns
- non-empty feed content
- usable stop coordinates
- trip and stop-time identifiers
- output row counts and uniqueness contracts

DART core tables are also persisted as normalized CSV outputs for validation and inspection.

## Cross-agency identifiers

GTFS identifiers are guaranteed to be unique only within a feed. Before combining agencies, the project namespaces stop and trip identifiers.

Examples:

- `dart:12345`
- `trinity:12345`

This prevents collisions between unrelated agency identifiers.

## Combined transit network

For the baseline network:

1. consecutive stop-time records within each trip are converted to directed stop-to-stop edges;
2. repeated observations of the same stop pair are summarized using median scheduled travel time;
3. nearby stops within 300 meters are connected with walking-transfer edges;
4. walking time assumes 4.8 km/h;
5. census-tract representative points and providers connect to nearby stops.

The resulting combined network is used for frequency-agnostic accessibility analysis.

## Schedule-aware routing

The temporal layer preserves actual scheduled departure and arrival times and applies service calendars and date-specific exceptions.

Current representative scenarios include:

- weekday morning at 8:00 AM
- weekday midday at 1:00 PM
- weekday evening at 6:00 PM
- Saturday midday at 1:00 PM

The model requires a rider to reach a stop before a usable departure, which makes it more conservative than the frequency-agnostic baseline.

See `docs/ACCESSIBILITY.md` for routing details.

## Interpretation

GTFS represents scheduled service, not observed operations.

The model does not currently incorporate:

- GTFS-Realtime vehicle positions or alerts
- observed delay distributions
- canceled trips not represented in the published schedule
- unexpected missed connections
- pedestrian-network barriers

Results therefore describe **scheduled transit accessibility**, not guaranteed door-to-door travel performance.

## Trinity Metro data notice

Data provided by Trinity Metro is not warranted by Trinity Metro for accuracy or completeness and is subject to change without notice.
