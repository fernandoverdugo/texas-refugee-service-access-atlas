# Texas Refugee Service Access Atlas

Geospatial decision-support platform for analyzing scheduled public-transit access to refugee-relevant services in Dallas and Tarrant Counties, Texas.

The project combines Census neighborhood context, verified service-provider locations, DART and Trinity Metro GTFS schedules, multimodal routing, service-specific accessibility, transparent gap classification, and facility-location optimization.

> **Core question:** Which Dallas–Fort Worth neighborhoods face the greatest barriers to reaching refugee-relevant services by public transit?

## Live application

**Interactive atlas:** https://texas-refugee-service-access-atlas.onrender.com

The atlas allows users to:

- shade census tracts by modeled nearest-provider travel time
- compare foreign-born population count and share, no-vehicle households, and poverty context
- toggle 30-, 45-, and 60-minute accessibility thresholds
- compare frequency-agnostic and schedule-aware transit scenarios
- filter access by service category
- inspect service-gap classifications
- view verified provider locations
- compare facility-location planning scenarios

The application is deployed as a Dockerized FastAPI service on Render and reads directly from the validated processed outputs in this repository.

## Analytical workflow

The project follows a staged analytical progression:

1. **Neighborhood context** — 2024 ACS 5-year tract-level demographic and transportation indicators
2. **Verified providers** — source-backed refugee-relevant service locations
3. **Multimodal transit network** — DART + Trinity Metro scheduled GTFS with nearby walking transfers
4. **Baseline accessibility** — generalized transit travel time without departure-specific waiting
5. **Schedule-aware accessibility** — time-of-day routing using actual scheduled departures
6. **Service-specific accessibility** — access to individual service categories rather than any provider
7. **Service-gap screening** — transparent access classifications combined with neighborhood context
8. **Facility-location optimization** — tract-level scenarios for improving coverage

## Study area and current data

The current study area contains **1,094 census tracts** across Dallas and Tarrant Counties.

| Measure | Current validated value |
| --- | ---: |
| Dallas County tracts | 645 |
| Tarrant County tracts | 449 |
| Verified refugee-service locations | 8 |
| Combined DART + Trinity Metro transit stops | 8,562 |
| Scheduled transit edges | 9,100 |
| Nearby walking-transfer edges | 38,198 |
| Tracts reaching at least one modeled provider | 568 |

The neighborhood panel represents approximately **4.79 million residents**, including approximately **1.02 million foreign-born residents**.

Foreign-born population is used only as neighborhood context. It is **not** treated as a refugee count or as a proxy for refugee residence.

## Accessibility results

### Frequency-agnostic baseline

The baseline model combines scheduled in-vehicle times, access/egress walking, nearby walking transfers, census-tract representative points, and the eight verified service locations.

| Measure | Dallas + Tarrant | Dallas County | Tarrant County |
| --- | ---: | ---: | ---: |
| Tracts in study area | 1,094 | 645 | 449 |
| Tracts reaching any modeled provider | 568 | 440 | 128 |
| Foreign-born population within 30 modeled minutes | 21.8% | 27.9% | 11.1% |
| Foreign-born population within 45 modeled minutes | 39.7% | 51.8% | 18.5% |
| Foreign-born population within 60 modeled minutes | 51.4% | 66.0% | 26.0% |

This is a network-potential baseline. It does not require a rider to arrive before a specific departure.

### Schedule-aware scenarios

The temporal model requires riders to reach stops in time for actual GTFS departures.

| Scenario | Foreign-born population within 45 scheduled minutes |
| --- | ---: |
| Weekday morning · 8:00 AM | 13.7% |
| Weekday midday · 1:00 PM | 16.2% |
| Weekday evening · 6:00 PM | 14.2% |
| Saturday midday · 1:00 PM | 14.8% |

The current GTFS feeds produced representative service dates of **December 2, 2026** for weekday scenarios and **December 5, 2026** for Saturday midday.

The difference from the 39.7% frequency-agnostic baseline illustrates the importance of service frequency and usable departure timing.

## Service-type accessibility

The atlas separates access by the type of service publicly documented for each provider.

| Service type | Provider locations | Foreign-born population within 45 modeled minutes |
| --- | ---: | ---: |
| Resettlement & case management | 8 | 39.7% |
| Education & English-language support | 6 | 39.2% |
| Employment | 6 | 39.7% |
| Health & behavioral health | 4 | 39.4% |
| Cash & benefits assistance | 4 | 37.9% |
| Immigration & legal support | 4 | **26.9%** |

Immigration and legal support show the largest modeled access gap in the current verified inventory.

The provider inventory includes **Church World Service (CWS) Dallas** at **1010 E Arapaho Rd., Suite 100, Richardson** as a separate organization from ICNA Relief Dallas.

## Service-access gap classification

The service-gap layer combines scheduled transit access with three neighborhood context indicators:

- foreign-born population
- population below poverty
- households with no vehicle

The rule set is intentionally transparent:

- **Lower gap:** at least one relevant provider within 45 scheduled minutes
- **Moderate gap:** none within 45 minutes, but at least one within 60
- **High gap:** none within 60 minutes
- tracts in the top quartile on at least two context indicators are elevated one level
- the maximum classification is **Severe gap**

For **weekday midday immigration/legal access**, the current model identifies:

- **185 severe-gap tracts**
- **728 high-gap tracts**
- **88 moderate-gap tracts**
- **93 lower-gap tracts**

These categories are planning-screening signals, not proof that a community or individual is unserved.

## Facility-location optimization

The project evaluates every transit-connected tract candidate to ask:

> If one additional refugee-service site could be added, which tract would improve 45-minute access for the largest currently underserved population?

For the foreign-born-population objective, the top modeled candidate is Dallas County tract `48113003102`.

- newly covered foreign-born population: **64,363**
- baseline foreign-born population coverage within 45 modeled minutes: **39.7%**
- optimized coverage with the candidate: **46.0%**
- modeled gain: **6.3 percentage points**

The project also compares objectives based on total population, no-vehicle households, and population below poverty. The selected tract changes under the poverty-weighted objective, illustrating that site-selection recommendations depend on the planning objective.

This is a **tract-level planning signal**, not a parcel recommendation. The model does not evaluate real-estate availability, cost, zoning, staffing, ownership, or agency feasibility.

## Architecture

```text
ACS + TIGER/Line          Provider sources            DART + Trinity Metro GTFS
       ↓                         ↓                              ↓
 tract context            verified inventory              transit network
       └───────────────────────┬───────────────────────────────┘
                               ↓
                     multimodal accessibility
                               ↓
              baseline + schedule-aware routing
                               ↓
                 service-specific accessibility
                               ↓
                    service-gap screening
                               ↓
                  facility-location scenarios
                               ↓
                     FastAPI + Leaflet atlas
```

## Repository structure

```text
data/processed/          validated analytical outputs
docs/                    methodology and source documentation
scripts/                 reproducible pipeline entry points
src/analysis/            network and accessibility logic
src/ingestion/           Census, geography, provider, and GTFS ingestion
src/optimization/        facility-location models
src/api/                 FastAPI service and Leaflet interface
tests/                   automated tests
.github/workflows/       CI and reproducible analytical builds
```

## Reproduce locally

### 1. Clone and install

```bash
git clone https://github.com/fernandoverdugo/texas-refugee-service-access-atlas.git
cd texas-refugee-service-access-atlas

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Run the tests

```bash
python -m pytest -q
```

### 3. Launch the committed validated application

The repository includes the processed outputs required by the live atlas.

```bash
uvicorn src.api.app:app --reload
```

Then open `http://127.0.0.1:8000`.

### 4. Rebuild source-dependent layers

A Census API key is optional for ordinary API requests but is required by the automated ACS refresh workflow.

```bash
export CENSUS_API_KEY="your_key_here"
python -m scripts.fetch_acs_dfw
python -m scripts.build_geography
python -m scripts.build_accessibility
python -m scripts.build_service_type_accessibility
python -m scripts.build_temporal_accessibility
python -m scripts.build_service_gaps
python -m scripts.optimize_facility_location
python -m scripts.optimize_equity_scenarios
```

The GitHub Actions workflows provide the authoritative automated build and validation path for refreshed source data.

## API

Interactive FastAPI documentation is available at:

- https://texas-refugee-service-access-atlas.onrender.com/docs
- https://texas-refugee-service-access-atlas.onrender.com/health

Selected endpoints include:

- `/api/summary`
- `/api/providers`
- `/api/service-types`
- `/api/service-accessibility/{service_type}`
- `/api/time-scenarios`
- `/api/temporal-accessibility/{scenario_id}`
- `/api/temporal-service-accessibility/{scenario_id}/{service_type}`
- `/api/service-gap-summary`
- `/api/service-gaps/{scenario_id}/{service_type}`
- `/api/service-gap-priorities/{scenario_id}/{service_type}`
- `/api/facility-location`
- `/api/facility-location/scenarios`

## Data sources

- **U.S. Census Bureau ACS 2024 5-year estimates** — tract-level neighborhood context
- **U.S. Census Bureau TIGER/Line 2024** — census-tract geometries
- **Dallas Area Rapid Transit (DART) GTFS** — Dallas-area scheduled transit
- **Trinity Metro GTFS** — Fort Worth/Tarrant-area scheduled transit
- **Public provider sources** — verification of refugee-relevant organizations, addresses, and services
- **OpenStreetMap / Nominatim fallback** — provider geocoding where required

See [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) for source definitions and interpretation constraints.

## Methodology documentation

- [Accessibility model](docs/ACCESSIBILITY.md)
- [Data sources](docs/DATA_SOURCES.md)
- [GTFS ingestion](docs/GTFS.md)
- [Provider inventory](docs/PROVIDERS.md)
- [Service types](docs/SERVICE_TYPES.md)
- [Service-gap classification](docs/SERVICE_GAPS.md)
- [Facility-location optimization](docs/FACILITY_LOCATION.md)

## Interpretation limits

The atlas measures one operational dimension of access: **scheduled public-transit accessibility to listed service locations**.

It does not measure:

- refugee population or individual refugee residence
- provider capacity
- appointment availability
- program eligibility
- language match
- service quality
- real-time transit reliability
- sidewalk quality or pedestrian barriers
- childcare, safety, disability access, or other household-level constraints

Outputs should therefore be interpreted as screening and planning evidence, not as definitive measures of unmet need.

## Technical principles

- use public, auditable sources
- separate observed data from planning assumptions
- preserve source provenance
- avoid treating foreign-born population as refugee population
- measure accessibility with network travel time rather than straight-line distance where possible
- expose assumptions and limitations
- build reproducible ingestion and validation before visualization
- test transformations and data contracts

## Technologies

Python · pandas · requests · GeoPandas · Shapely · NetworkX · FastAPI · Leaflet · Docker · pytest · GitHub Actions

## Project status

| Capability | Status |
| --- | --- |
| ACS tract context | ✅ Implemented |
| TIGER/Line tract geography | ✅ Implemented |
| Verified provider inventory | ✅ Implemented |
| DART GTFS ingestion | ✅ Implemented |
| Trinity Metro GTFS ingestion | ✅ Implemented |
| Multimodal transit graph | ✅ Implemented |
| Baseline accessibility | ✅ Implemented |
| Schedule-aware accessibility | ✅ Implemented |
| Service-type accessibility | ✅ Implemented |
| Service-gap classification | ✅ Implemented |
| Interactive atlas + API | ✅ Live deployment |
| Facility-location optimization | ✅ Implemented |

Potential future extensions include real-time transit reliability, richer pedestrian-network routing, provider-capacity data, and broader Texas metro coverage.

## License

MIT

## Trinity Metro data notice

Data provided by Trinity Metro is not warranted by Trinity Metro for accuracy or completeness and is subject to change without notice.

Geocoding fallback attribution: © OpenStreetMap contributors (Nominatim / ODbL).
