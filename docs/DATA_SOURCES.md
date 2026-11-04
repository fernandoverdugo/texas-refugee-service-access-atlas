# Data sources

This project combines public demographic, geographic, transit, and provider-location sources. Each source is treated as a versioned analytical input, and the repository separates observed data from modeling assumptions.

## U.S. Census Bureau — American Community Survey

**Dataset:** 2024 ACS 5-year Detailed Tables  
**Geography:** census tract  
**Study area:** Dallas County and Tarrant County, Texas  
**API base:** `https://api.census.gov/data/2024/acs/acs5`

The ACS 5-year product is used because tract-level estimates are available across the full study area.

| Variable | Project field | Interpretation |
| --- | --- | --- |
| B01003_001E | population | Total tract population |
| B05002_013E | foreign_born_population | Foreign-born population |
| B17001_002E | population_below_poverty | Population below poverty level |
| B08201_002E | households_no_vehicle | Households with no vehicle available |
| B25003_003E | renter_occupied_households | Renter-occupied housing units |

These measures describe neighborhood context. **Foreign-born population is not a proxy for refugee population**, and the indicators are not combined into an undocumented refugee-need score.

## U.S. Census Bureau — TIGER/Line

**Dataset:** 2024 Texas census-tract boundaries  
**Source:** `https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_48_tract.zip`

TIGER/Line provides the tract geometries used by the atlas and the representative points used as routing origins.

The pipeline filters the statewide tract file to Dallas and Tarrant Counties and joins it one-to-one to the ACS tract panel by GEOID.

## Dallas Area Rapid Transit

**Source:** official DART GTFS Schedule feed  
**Feed:** `https://www.dart.org/transitdata/latest/google_transit.zip`

The DART feed provides scheduled Dallas-area bus, light rail, Trinity Railway Express, trolley, and streetcar service.

The project uses stops, trips, stop times, routes, calendars, and service-date exceptions as required by the baseline and schedule-aware routing layers.

## Trinity Metro

**Source:** official Trinity Metro GTFS feed  
**Feed:** `https://gtfsdata.ridetm.org/gtfs/fwtatransitdata.zip`

Trinity Metro is required because the study area includes Tarrant County. A DART-only network would systematically understate scheduled transit access in the western half of the study area.

DART and Trinity Metro identifiers are namespaced before the feeds are combined to prevent cross-agency identifier collisions.

### Trinity Metro data notice

Data provided by Trinity Metro is not warranted by Trinity Metro for accuracy or completeness and is subject to change without notice.

## Refugee-relevant service locations

The provider inventory contains locations with a current, publicly verifiable organizational source.

A provider is included only when a public source supports:

1. a physical service location;
2. refugee-specific services or resettlement activity;
3. a location in Dallas or Tarrant County; and
4. source provenance that can be preserved for later verification.

The inventory currently includes eight verified locations and normalizes publicly documented services into categories for resettlement/case management, employment, education, health, immigration/legal support, and cash/benefits assistance.

Provider presence does not imply capacity, eligibility, language availability, appointment availability, or service quality.

See `docs/PROVIDERS.md` for provider-specific documentation.

## Geocoding fallback

Provider addresses are resolved from verified source records. Where a geocoding fallback is required, the project uses Nominatim / OpenStreetMap and preserves the resulting attribution.

Geocoding fallback attribution: © OpenStreetMap contributors (Nominatim / ODbL).

## Geographic and analytical interpretation

The project measures **scheduled public-transit accessibility**, not service quality or outcomes.

A geographically reachable location may still be inaccessible because of:

- eligibility rules
- appointment availability
- language availability
- disability access
- childcare
- pedestrian conditions
- safety
- transit reliability
- other household-level barriers

Accessibility results should therefore be interpreted as one operational planning dimension rather than a comprehensive measure of service availability or individual need.
