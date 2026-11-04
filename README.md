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

DART GTFS data will provide scheduled:

- stops
- routes
- trips
- stop times
- service calendars

The transit layer will support travel-time, transfer, and reachability analysis.

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

**Phase 1A — ACS neighborhood context**

The repository currently implements the first reproducible ingestion layer for 2024 ACS 5-year census-tract data in Dallas and Tarrant Counties.

The initial ingestion module:

- queries the Census Data API
- validates required fields
- normalizes tract identifiers
- derives human-readable county and tract keys
- preserves raw ACS estimates without inventing composite scores
- supports a `CENSUS_API_KEY` environment variable

Transit and service-location ingestion are the next milestones.

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

Python · pandas · requests · GeoPandas · Shapely · NetworkX · pytest · GitHub Actions

## Roadmap

| Phase | Status |
| --- | --- |
| ACS tract-level context | 🚧 In progress |
| Provider inventory | ⏳ Next |
| DART GTFS ingestion | ⏳ Planned |
| Transit graph + routing | ⏳ Planned |
| Accessibility metrics | ⏳ Planned |
| Interactive atlas | ⏳ Planned |
| Facility-location optimization | ⏳ Planned |

## License

MIT
