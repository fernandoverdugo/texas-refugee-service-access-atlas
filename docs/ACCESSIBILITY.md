# Multimodal DFW accessibility model

The accessibility system uses official GTFS schedule feeds from:

1. **Dallas Area Rapid Transit (DART)** for Dallas-area bus, light rail, TRE, trolley, and streetcar service.
2. **Trinity Metro** for Fort Worth/Tarrant-area transit service.

A DART-only network would systematically understate transit access in Tarrant County, so both feeds are required for the Dallas–Tarrant study area.

## Cross-agency identifiers

GTFS identifiers are unique only within a feed. Stop and trip identifiers are namespaced before the feeds are combined.

Examples:

- `dart:12345`
- `trinity:12345`

## Origins and destinations

Census tract representative points are used as tract-level routing origins.

Verified refugee-service locations are routing destinations. Tracts and providers connect to up to three transit stops within one kilometer, and access/egress walking time is included in generalized travel time.

These are tract-level planning abstractions rather than modeled household doorsteps.

## Frequency-agnostic baseline

For each trip, consecutive stop-time records are converted into directed stop-to-stop edges. Repeated observations of a stop pair are summarized with median scheduled in-vehicle time.

Stops within 300 meters are connected by walking-transfer edges using a 4.8 km/h walking-speed assumption. This supports transfers within and between agencies where the networks meet.

For each census tract, the baseline calculates:

- nearest reachable provider travel time
- providers reachable within 30 minutes
- providers reachable within 45 minutes
- providers reachable within 60 minutes
- total reachable providers

This baseline is **frequency-agnostic**: it represents network travel-time potential but does not require arrival before a specific scheduled departure.

## Schedule-aware routing

The project also includes a time-dependent routing layer based on:

- `trips.txt`
- `stop_times.txt`
- `calendar.txt`
- `calendar_dates.txt`

for both DART and Trinity Metro.

For each scenario, the pipeline selects a common active service date across both feeds, applies weekly calendars and date-specific exceptions, and evaluates actual scheduled connections.

### Representative scenarios

- Weekday morning: 8:00 AM
- Weekday midday: 1:00 PM
- Weekday evening: 6:00 PM
- Saturday midday: 1:00 PM

The current published feeds produced representative dates of **December 2, 2026** for weekday scenarios and **December 5, 2026** for Saturday midday.

### Routing method

The temporal model uses a backward scheduled-connection scan.

For each provider and travel-time threshold:

1. begin from the provider's nearby transit stops;
2. subtract final walking time from the threshold deadline;
3. scan GTFS connections backward by scheduled arrival time;
4. accept a connection only when its arrival can still reach the destination before the deadline;
5. propagate nearby walking-transfer opportunities backward;
6. count an origin tract as reachable only when its access walk reaches a stop before the latest feasible departure.

A rider who reaches a stop after the bus or train leaves does not receive credit for that trip.

## Baseline results

Foreign-born population with at least one verified provider within:

| Threshold | Dallas + Tarrant |
| --- | ---: |
| 30 modeled minutes | 21.8% |
| 45 modeled minutes | 39.7% |
| 60 modeled minutes | 51.4% |

## Schedule-aware results

Foreign-born population with at least one verified provider reachable within 45 scheduled minutes:

| Scenario | 45-minute coverage |
| --- | ---: |
| Weekday morning | 13.7% |
| Weekday midday | 16.2% |
| Weekday evening | 14.2% |
| Saturday midday | 14.8% |

The lower schedule-aware percentages are expected because the temporal model also requires a usable departure after the rider reaches the stop.

## Service-specific accessibility

The same routing framework is applied separately to normalized provider service categories.

This prevents a tract from receiving credit for access to an unrelated service merely because some refugee-relevant provider is nearby.

The current categories are:

- resettlement & case management
- employment
- education & English-language support
- health & behavioral health
- immigration & legal support
- cash & benefits assistance

## Interpretation limits

Both routing layers measure **scheduled transit accessibility**, not actual trip performance or individual service use.

The models do not currently account for:

- real-time delay
- canceled trips not represented in schedule data
- reliability distributions
- unexpected missed connections
- detailed pedestrian-network barriers
- provider capacity
- appointment availability
- program eligibility
- language match
- service quality
- household-level travel constraints

The results should therefore be interpreted as planning and screening evidence rather than guaranteed travel time or a definitive measure of unmet need.

## Trinity Metro data notice

Data provided by Trinity Metro is not warranted by Trinity Metro for accuracy or completeness and is subject to change without notice.
