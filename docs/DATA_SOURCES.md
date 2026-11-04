# Data sources

## U.S. Census Bureau — American Community Survey

**Dataset:** 2024 ACS 5-year Detailed Tables  
**Geography:** census tract  
**Initial study area:** Dallas County and Tarrant County, Texas  
**API base:** `https://api.census.gov/data/2024/acs/acs5`

The ACS 5-year product is used because tract-level estimates are available for the entire study area.

### Initial fields

| Variable | Project field | Interpretation |
| --- | --- | --- |
| B01003_001E | population | Total tract population |
| B05002_013E | foreign_born_population | Foreign-born population |
| B17001_002E | population_below_poverty | Population below poverty level |
| B08201_002E | households_no_vehicle | Households with no vehicle available |
| B25003_003E | renter_occupied_households | Renter-occupied housing units |

These measures describe neighborhood context. **Foreign-born population is not a proxy for refugee population**, and the indicators should not be combined into an undocumented "refugee need score."

The Census Bureau documents 2024 ACS 5-year data as available down to census tracts and, for detailed tables, block groups.

## Dallas Area Rapid Transit

**Planned source:** DART General Transit Feed Specification (GTFS)

The transit layer will preserve the core GTFS entities required for scheduled routing:

- stops
- routes
- trips
- stop times
- calendars / service dates

The first network model will use scheduled travel time. Real-time vehicle data are outside the initial scope.

## Refugee-relevant service locations

Service records will be added only when a public source can verify the location and service category.

Planned categories include:

- resettlement / case management
- refugee health
- behavioral health
- employment
- English-language instruction
- benefits / social services

Provider presence does not imply capacity, eligibility, language availability, or appointment availability. Those dimensions will be modeled only when verified data exist.

## Geographic interpretation

The project measures **accessibility**, not service quality or outcomes. A location that is geographically reachable may still be inaccessible because of eligibility rules, scheduling, language, disability access, childcare, safety, or other barriers.

Travel-time analysis should therefore be interpreted as one operational dimension of access rather than a comprehensive measure of service availability.
