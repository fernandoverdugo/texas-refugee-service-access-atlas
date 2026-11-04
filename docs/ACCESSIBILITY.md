# Multimodal DFW accessibility model

The accessibility layer uses two official GTFS schedule feeds:

1. **Dallas Area Rapid Transit (DART)** for Dallas-area bus, light rail, TRE, trolley, and streetcar service.
2. **Trinity Metro** for Fort Worth/Tarrant-area transit service.

A DART-only network would systematically understate transit access in Tarrant County, so both feeds are required for the Dallas–Tarrant study area.

## Cross-agency identifiers

GTFS identifiers are only guaranteed to be unique within a feed. The project namespaces stop and trip identifiers before combining agencies.

Examples:

- `dart:12345`
- `trinity:12345`

This prevents accidental collisions between unrelated identifiers.

## Scheduled transit edges

For each trip, consecutive stop-time records are converted into directed stop-to-stop edges. Repeated observations of the same stop pair are summarized with median scheduled travel time.

This first model is frequency-agnostic. It represents scheduled in-vehicle travel time but does not yet model wait time for a particular departure.

## Walking transfers

Stops within 300 meters are connected by walking-transfer edges using a 4.8 km/h walking-speed assumption. These connections support transfers within an agency and between DART and Trinity Metro where their networks meet.

## Origins and destinations

Census tract representative points and verified refugee-service locations connect to up to three transit stops within one kilometer. Access and egress walking time are included in total generalized travel time.

## First accessibility metrics

For each census tract the model calculates:

- nearest reachable refugee-service provider travel time
- providers reachable within 30 minutes
- providers reachable within 45 minutes
- providers reachable within 60 minutes
- total reachable providers

## Interpretation limits

The model measures scheduled transit accessibility, not actual trip performance. It does not yet account for:

- departure-time-specific waiting
- missed connections
- real-time delays
- demand-responsive transit
- appointment availability
- program eligibility
- language availability
- sidewalk quality or pedestrian barriers

Those limitations are intentionally documented before any public-facing accessibility score is presented.

## Trinity Metro data notice

Data provided by Trinity Metro is not warranted by Trinity Metro for accuracy or completeness and data is subject to change without notice.

The reproducible build retrieves the current official feed so public outputs can be refreshed when schedules change.


## Time-dependent routing

The project now includes a schedule-aware routing layer in addition to the original frequency-agnostic baseline.

The temporal model uses:

- `trips.txt`
- `stop_times.txt`
- `calendar.txt`
- `calendar_dates.txt`

for both DART and Trinity Metro.

For each scenario, the pipeline selects a recent common active service date across both feeds, applies weekly service calendars and date-specific exceptions, and evaluates actual scheduled connections.

### Representative scenarios

- Weekday morning: 8:00 AM
- Weekday midday: 1:00 PM
- Weekday evening: 6:00 PM
- Saturday midday: 1:00 PM

The current published feeds produced representative dates of December 2, 2026 for weekday scenarios and December 5, 2026 for Saturday midday.

### Routing method

The model uses a backward scheduled-connection scan.

For each provider and travel-time threshold:

1. begin from the provider's nearby transit stops;
2. subtract final walking time from the threshold deadline;
3. scan GTFS transit connections backward by scheduled arrival time;
4. accept a connection only when its arrival can still reach the destination before the deadline;
5. propagate nearby walking-transfer opportunities backward;
6. count an origin tract as reachable only when its access walk reaches a stop before the latest feasible departure.

This means a rider who reaches a stop after the bus or train leaves does not receive credit for that trip.

### Current overall results

Foreign-born population with at least one verified provider reachable within 45 scheduled minutes:

| Scenario | 45-minute coverage |
| --- | ---: |
| Weekday morning | 18.4% |
| Weekday midday | 17.0% |
| Weekday evening | 18.1% |
| Saturday midday | 15.5% |

The earlier frequency-agnostic 45-minute baseline was 39.7%. The difference is expected: the baseline measures network travel-time potential, while the temporal model also requires a usable scheduled departure.

### Interpretation limits

The temporal layer still does not model:

- real-time delay
- canceled trips
- reliability distributions
- unexpected missed connections
- walking-network barriers
- service eligibility or appointment availability

It should therefore be interpreted as **scheduled accessibility**, not guaranteed door-to-door travel time.
