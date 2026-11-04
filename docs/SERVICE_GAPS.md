# Service-access gap classification

## Purpose

The service-access gap layer converts scheduled transit accessibility into a small set of transparent planning categories.

It is designed to answer:

> Which tracts combine poor scheduled access to a selected service type with relatively high concentrations of population characteristics associated with greater transit-service vulnerability?

The classification is intentionally rule-based rather than a weighted composite score.

## Context thresholds

The model uses study-area 75th-percentile cutoffs:

| Indicator | 75th-percentile threshold |
| --- | ---: |
| Foreign-born population | 1,307 residents |
| Population below poverty | 736.75 residents |
| Households with no vehicle | 128.75 households |

A tract receives one context flag for each indicator at or above its threshold.

A tract has **elevated context** when at least two of the three flags are present.

These are aggregate planning indicators. They are not refugee counts and do not imply individual-level need.

## Base access classification

For a selected scheduled transit scenario and service type:

- **Lower gap**: at least one relevant provider is reachable within 45 minutes.
- **Moderate gap**: no relevant provider is reachable within 45 minutes, but at least one is reachable within 60 minutes.
- **High gap**: no relevant provider is reachable within 60 minutes.

## Context elevation

If a tract has elevated context, its base access classification is elevated by one level:

- Lower → Moderate
- Moderate → High
- High → Severe

The maximum classification is **Severe gap**.

This produces four final classes:

1. Lower gap
2. Moderate gap
3. High gap
4. Severe gap

## Example

A tract with:

- no immigration/legal provider within 60 scheduled minutes;
- foreign-born population above the 75th percentile;
- no-vehicle households above the 75th percentile;

receives a base classification of **High gap** and is elevated to **Severe gap** because it has at least two high-context indicators.

## Priority ranking

For each time scenario and service type, the project publishes the top 25 priority tracts.

Ranking is deterministic and ordered by:

1. gap level;
2. number of high-context indicators;
3. foreign-born population;
4. no-vehicle households;
5. population below poverty;
6. tract GEOID.

The rank is a screening tool for deeper planning analysis, not a recommendation to target individuals or infer refugee residence.

## Current weekday-midday example

For immigration and legal support at the weekday-midday scenario:

- 185 tracts are classified **Severe gap**
- 728 tracts are classified **High gap**
- 88 tracts are classified **Moderate gap**
- 93 tracts are classified **Lower gap**

The large number of high/severe tracts reflects limited scheduled transit access to the **four verified immigration/legal locations** in the current inventory and the conservative schedule-aware routing model.

## Limitations

The classification does not account for:

- provider capacity
- appointment availability
- language match
- eligibility
- real-time transit reliability
- sidewalk or pedestrian-network quality
- household-level characteristics
- unlisted or informal service providers

It should be interpreted as a **service-system screening layer**, not a definitive measure of unmet need.
