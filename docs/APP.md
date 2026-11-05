# Interactive Atlas application

## Purpose

The browser application turns the validated accessibility outputs into an interactive planning interface for Dallas and Tarrant Counties.

It is designed to help users move from a broad map view to a specific planning question without changing the underlying analysis.

## Main controls

Users can select:

- map metric
- 30-, 45-, or 60-minute access threshold
- service type
- frequency-agnostic or schedule-aware transit scenario
- facility-location planning objective

The map updates the tract shading, provider layer, legend, service-gap counts, and planning summaries to reflect the current selection.

## Dynamic decision summary

The **What this selection means** panel converts the current service and time selection into a concise planning statement.

For scheduled scenarios it reports:

- selected service type and transit scenario
- foreign-born population share modeled within 45 scheduled minutes
- severe-gap tract count
- high-gap tract count

The summary is descriptive planning evidence, not a claim of individual unmet need.

## Network potential vs scheduled reality

The Atlas explicitly compares two different accessibility concepts:

- **Frequency-agnostic baseline:** network travel-time potential without departure-specific waiting
- **Scheduled access:** actual published GTFS departures for a representative service date and time

The interface displays both 45-minute foreign-born coverage values and the percentage-point change.

This comparison is important because a transit network may appear geographically connected while published service frequency makes practical access much lower.

## Facility-location comparison

For each planning objective, the one-site scenario displays:

- candidate tract
- current objective coverage
- modeled coverage with the candidate
- newly covered objective population/households
- number of tracts newly gaining modeled access
- percentage-point coverage gain

The candidate is a tract-level representative point and is not a parcel recommendation.

## CSV exports

The interface supports four browser-generated exports:

- **Current tract view CSV** — tract context plus the currently selected service/time accessibility and gap fields
- **Gap priorities CSV** — top priority tracts for the selected scheduled service scenario
- **Facility scenario CSV** — the currently selected one-site optimization scenario
- **Provider inventory CSV** — the verified provider inventory shown in the Atlas

Exports use the same API data already displayed in the interface and do not create a separate analytical calculation path.

## Interpretation boundary

The Atlas measures scheduled public-transit accessibility to listed service providers.

It does not estimate refugee population, provider capacity, eligibility, appointment availability, language match, service quality, or real-time transit reliability.

The interface is therefore a service-system screening and planning tool, not a placement or individual-level decision system.
