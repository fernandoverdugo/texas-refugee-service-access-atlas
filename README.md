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

The application is deployed as a Dockerized FastAPI service on Render.

## Interactive atlas

The repository includes an interactive web atlas built with FastAPI and Leaflet. The interface allows users to:

- shade census tracts by modeled nearest-provider travel time
- inspect foreign-born population, no-vehicle households, and poverty context
- toggle 30-, 45-, and 60-minute provider-access thresholds
- view verified refugee-service provider locations
- click individual tracts for population and accessibility details

The interface reads directly from the validated processed outputs, so refreshed analytical data flow into the application without maintaining a separate visualization dataset.

## Planned outputs

The first accessibility metrics will include:

- number of relevant services reachable within 30, 45, and 60 minutes
- estimated transit travel time to the nearest service
- number of transfers required
- population-weighted accessibility scores
- identification of potential service deserts

A later phase will evaluate candidate service locations using facility-location optimization.

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
| Accessibility metrics | ✅ Baseline implemented |
| Interactive atlas | ✅ Live deployment |
| Facility-location optimization | ⏳ Planned |

## License

MIT


## Trinity Metro data notice

Data provided by Trinity Metro is not warranted by Trinity Metro for accuracy or completeness and data is subject to change without notice.

Geocoding fallback attribution: © OpenStreetMap contributors (Nominatim / ODbL).
