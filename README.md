# Texas Refugee Service Access Atlas

Geospatial and transit-network analysis of refugee service accessibility, mobility gaps, and service deserts in Dallas–Fort Worth.

## Project objective

Refugee resettlement organizations need to know more than whether services exist. They also need to understand whether clients can realistically reach healthcare, employment, language, and resettlement services without reliable access to a car.

This project develops a reproducible accessibility-analysis platform that combines:

- Census neighborhood context
- refugee-relevant service locations
- public-transit schedules and stops
- travel-time and transfer calculations
- geospatial accessibility metrics
- service-gap identification
- future facility-location optimization

The initial study area is **Dallas and Tarrant Counties**. The architecture is designed to expand to the wider Dallas–Fort Worth region and other Texas resettlement metros.

## Core research question

> Which Dallas–Fort Worth neighborhoods face the greatest barriers to reaching refugee-relevant services by public transit?

## Planned analytical layers

### 1. Neighborhood context

The first layer uses the 2024 American Community Survey 5-year estimates at census-tract level to measure characteristics relevant to service accessibility, including:

- total population
- foreign-born population
- limited-English-proficiency indicators
- poverty
- households without a vehicle
- renter households

These indicators describe potential accessibility needs. They are not treated as measures of refugee population or as causal explanations of service use.

### 2. Service locations

The project will create a documented provider inventory for refugee-relevant services such as:

- refugee resettlement and case management
- health and behavioral health
- employment services
- English-language instruction
- public benefits and social services

Only locations with a verifiable public source will be included.

### 3. Transit network

The DFW transit layer combines official GTFS schedule feeds from:

- Dallas Area Rapid Transit (DART)
- Trinity Metro

The combined model uses scheduled stops, trips, stop times, and nearby walking-transfer links so Dallas and Tarrant County are not evaluated with a Dallas-only network.

## First accessibility baseline

The first validated multimodal model combines DART and Trinity Metro scheduled GTFS data, nearby walking transfers, tract representative points, and the seven verified refugee-service locations.

| Measure | Dallas + Tarrant | Dallas County | Tarrant County |
| --- | ---: | ---: | ---: |
| Tracts in study area | 1,094 | 645 | 449 |
| Tracts reaching any modeled provider | 568 | 440 | 128 |
| Foreign-born population with a provider within 30 modeled minutes | 21.8% | 27.9% | 11.1% |
| Foreign-born population with a provider within 45 modeled minutes | 39.7% | 51.8% | 18.5% |
| Foreign-born population with a provider within 60 modeled minutes | 51.4% | 66.0% | 26.0% |

These figures are a **scheduled-accessibility baseline**, not observed travel behavior. The current graph uses median scheduled in-vehicle times, walking access/egress and nearby walking transfers, but it does not yet model departure-time-specific waiting, missed connections, real-time delays, service eligibility, appointment availability, or pedestrian conditions.

The Dallas–Tarrant difference should therefore be interpreted as a signal for deeper service-access analysis rather than a definitive measure of refugee access.

## Live demo

**Interactive atlas:** https://texas-refugee-service-access-atlas.onrender.com

- API documentation: https://texas-refugee-service-access-atlas.onrender.com/docs
- Health check: https://texas-refugee-service-access-atlas.onrender.com/health
- Summary API: https://texas-refugee-service-access-atlas.onrender.com/api/summary
- Facility-location recommendation API: https://texas-refugee-service-access-atlas.onrender.com/api/facility-location
- Equity-aware facility scenarios API: https://texas-refugee-service-access-atlas.onrender.com/api/facility-location/scenarios
- Service-type summary API: https://texas-refugee-service-access-atlas.onrender.com/api/service-types
- Service accessibility API: `/api/service-accessibility/{service_type}`
- Time-scenario API: `/api/time-scenarios`
- Time-dependent accessibility API: `/api/temporal-accessibility/{scenario_id}`
- Time-dependent service accessibility API: `/api/temporal-service-accessibility/{scenario_id}/{service_type}`
- Service-gap summary API: `/api/service-gap-summary`
- Service-gap tract API: `/api/service-gaps/{scenario_id}/{service_type}`
- Service-gap priorities API: `/api/service-gap-priorities/{scenario_id}/{service_type}`

The application is deployed as a Dockerized FastAPI service on Render.

## Interactive atlas

The repository includes an interactive web atlas built with FastAPI and Leaflet. The interface allows users to:

- shade census tracts by modeled nearest-provider travel time
- inspect foreign-born population, foreign-born share of population, no-vehicle households, and poverty context
- toggle 30-, 45-, and 60-minute provider-access thresholds
- compare frequency-agnostic and schedule-aware time-of-day routing
- shade tracts by transparent service-access gap classification
- view verified refugee-service provider locations
- click individual tracts for population and accessibility details

The interface reads directly from the validated processed outputs, so refreshed analytical data flow into the application without maintaining a separate visualization dataset.


The atlas provides both **foreign-born population count** and **foreign-born share of population**. The count highlights tracts with the largest absolute foreign-born populations, while the share highlights neighborhoods where foreign-born residents make up a larger proportion of the total population.

## Time-dependent transit accessibility

The atlas now includes schedule-aware routing scenarios that require riders to reach stops in time for actual GTFS departures.

| Scenario | Foreign-born population within 45 scheduled minutes |
| --- | ---: |
| Weekday morning · 8:00 AM | **13.7%** |
| Weekday midday · 1:00 PM | **16.2%** |
| Weekday evening · 6:00 PM | **14.2%** |
| Saturday midday · 1:00 PM | **14.8%** |

The earlier frequency-agnostic 45-minute baseline was **39.7%**. That baseline measures network travel-time potential; the time-dependent model is more conservative because it also accounts for whether a usable scheduled departure exists after the rider reaches the stop.

The current GTFS feeds produced representative service dates of **December 2, 2026** for weekday scenarios and **December 5, 2026** for Saturday midday.

## Service-type accessibility

The atlas can now analyze access to specific service categories rather than treating every provider as interchangeable.

| Service type | Provider locations | Foreign-born population within 45 modeled minutes |
| --- | ---: | ---: |
| Resettlement & case management | 7 | 39.7% |
| Education & English-language support | 5 | 39.2% |
| Employment | 5 | 39.1% |
| Health & behavioral health | 3 | 36.9% |
| Cash & benefits assistance | 3 | 35.9% |
| Immigration & legal support | 3 | **24.1%** |

Immigration and legal support show the largest modeled access gap in the current verified provider inventory.

The service-type filter updates tract reachability, nearest-service travel time, provider markers, and tract popup metrics together. These results describe scheduled transit access to listed service locations; they do not measure provider capacity, appointment availability, eligibility, language match, or service quality.

## Service-access gap classification

The atlas includes a transparent screening layer that combines scheduled transit access with neighborhood context.

The rule set is intentionally simple:

- **Lower gap:** at least one relevant provider within 45 scheduled minutes
- **Moderate gap:** no provider within 45 minutes, but at least one within 60
- **High gap:** no relevant provider within 60 minutes
- tracts in the top quartile on at least two of three context indicators—foreign-born population, poverty population, and no-vehicle households—are elevated one level

Current 75th-percentile context thresholds are:

- foreign-born population: **1,307**
- population below poverty: **736.75**
- no-vehicle households: **128.75**

For **weekday midday immigration/legal access**, the current classification identifies:

- **189 severe-gap tracts**
- **750 high-gap tracts**
- **92 moderate-gap tracts**
- **63 lower-gap tracts**

These classes are planning-screening categories, not measures of individual refugee need or proof that a community is unserved.

## Facility-location optimization

The first planning optimization asks:

> If one additional refugee-service site could be added, which transit-connected tract would improve 45-minute access for the largest currently underserved foreign-born population?

The exact one-site maximum-coverage model evaluates every transit-connected tract candidate.

**Top modeled candidate:** Dallas County tract `48113003102`

- newly covered foreign-born population: **64,363**
- newly covered total population: **287,188**
- newly covered no-vehicle households: **10,253**
- newly covered tracts: **64**
- baseline foreign-born population with a provider within 45 modeled minutes: **39.7%**
- optimized coverage with the candidate: **46.0%**
- modeled gain: **6.3 percentage points**

This is a **tract-level planning signal**, not a parcel recommendation. The model does not evaluate real-estate availability, cost, zoning, staffing, ownership, or agency feasibility.


### Equity-aware scenario comparison

Using the same 45-minute network and candidate set, the project compares how the selected tract changes under different planning objectives.

| Objective | Top tract | County | Newly covered objective | Baseline coverage | With candidate | Gain |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Foreign-born population | `48113003102` | Dallas | 64,363 residents | 39.7% | 46.0% | +6.3 pp |
| Total population | `48113003102` | Dallas | 287,188 residents | 32.5% | 38.5% | +6.0 pp |
| No-vehicle households | `48113003102` | Dallas | 10,253 households | 45.0% | 54.9% | +10.0 pp |
| Population below poverty | `48113008701` | Dallas | 59,535 residents | 37.4% | 47.3% | +10.0 pp |

Three objectives select the same tract, while the poverty-weighted objective shifts the recommendation to `48113008701`. Site-selection results are therefore conditional on the planning objective rather than a single universally best location.

## Analytical outputs

Current outputs include:

- relevant service locations reachable within 30, 45, and 60 minutes
- modeled travel time to the nearest service
- service-type-specific accessibility
- population-weighted access summaries
- neighborhood service-gap classifications and ranked priority tracts
- one-site facility-location optimization
- equity-aware site-selection scenarios

Departure-time-specific waiting and explicit transfer-count metrics remain future enhancements.

## Architecture

```text
Census ACS                  Service directories              DART GTFS
    ↓                              ↓                            ↓
tract context                 provider inventory             transit graph
    └───────────────┬──────────────┴──────────────┬────────────┘
                    ↓
              geospatial joins
                    ↓
          transit accessibility model
                    ↓
       neighborhood access indicators
                    ↓
             interactive atlas
                    ↓
      facility-location optimization
```

## Current milestone

**Phase 1 — Core analytical layers**

The repository now includes a validated 2024 ACS tract panel for Dallas and Tarrant Counties and a source-backed inventory of refugee-service providers.

Current validated data:

- 1,094 census tracts
- 645 Dallas County tracts
- 449 Tarrant County tracts
- approximately 4.79 million residents represented
- approximately 1.02 million foreign-born residents represented
- 7 verified refugee-service locations across the two counties

The DART GTFS ingestion layer is implemented and validated against DART's current official fixed-route schedule feed.

Current validated transit feed:

- 6,978 stops
- 92 routes
- 20,124 trips
- 961,975 stop-time records

## Repository structure

```text
data/
  processed/          normalized analytical datasets
docs/                 data and methodology documentation
scripts/              reproducible pipeline runners
src/
  ingestion/          Census, GTFS, and provider ingestion
tests/                automated tests
.github/workflows/    continuous integration
```

## Technical principles

- use public, auditable sources
- separate observed data from planning assumptions
- avoid treating foreign-born or language indicators as refugee counts
- measure accessibility with travel time rather than straight-line distance where possible
- preserve source provenance
- build reusable ingestion and validation before visualization
- test transformations and data contracts

## Data sources

- U.S. Census Bureau American Community Survey 5-year estimates
- Dallas Area Rapid Transit GTFS
- verified public service-provider directories

See `docs/DATA_SOURCES.md` for source definitions and interpretation constraints.

## Technologies

Python · pandas · requests · GeoPandas · Shapely · NetworkX · FastAPI · Leaflet · Docker · pytest · GitHub Actions

## Roadmap

| Phase | Status |
| --- | --- |
| ACS tract-level context | ✅ Implemented |
| Provider inventory | ✅ Implemented |
| DART GTFS ingestion | ✅ Implemented |
| Trinity Metro GTFS ingestion | ✅ Implemented |
| Transit graph + routing | ✅ Implemented |
| Accessibility metrics | ✅ Baseline + service-type + time-dependent metrics implemented |
| Interactive atlas | ✅ Live deployment |
| Facility-location optimization | ✅ One-site + equity-aware scenarios implemented |

## License

MIT


## Trinity Metro data notice

Data provided by Trinity Metro is not warranted by Trinity Metro for accuracy or completeness and data is subject to change without notice.

Geocoding fallback attribution: © OpenStreetMap contributors (Nominatim / ODbL).
