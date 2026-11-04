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
