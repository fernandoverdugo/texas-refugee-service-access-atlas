# Service-type accessibility

## Purpose

The first accessibility model treats every verified refugee-service location as a general destination. This layer separates access by the type of service a provider publicly advertises.

The goal is to answer a more operational question:

> Can residents reach the specific kind of refugee-relevant service they may need, not merely any provider location?

## Normalized service types

Raw provider tags are normalized into six public-facing categories:

| Service type | Raw categories included |
| --- | --- |
| Resettlement & case management | resettlement, case_management, refugee_services, resource_navigation, family_assistance |
| Employment | employment |
| Education & English-language support | education |
| Health & behavioral health | health_support, mental_health |
| Immigration & legal support | immigration |
| Cash & benefits assistance | cash_assistance |

The normalization is intentionally conservative. Categories are assigned only when the source-backed provider inventory already identifies the corresponding service.

## Current provider counts

- Resettlement & case management: 7 locations
- Employment: 5 locations
- Education & English-language support: 5 locations
- Health & behavioral health: 3 locations
- Immigration & legal support: 3 locations
- Cash & benefits assistance: 3 locations

## First 45-minute findings

Using the same DART + Trinity Metro scheduled-transit model:

| Service type | Foreign-born population within 45 modeled minutes |
| --- | ---: |
| Resettlement & case management | 39.7% |
| Education & English-language support | 39.2% |
| Employment | 39.1% |
| Health & behavioral health | 36.9% |
| Cash & benefits assistance | 35.9% |
| Immigration & legal support | 24.1% |

The immigration/legal category has the largest modeled access gap in the current provider inventory.

These percentages describe scheduled transit access to the listed service locations. They do not measure provider capacity, appointment availability, language match, eligibility, service quality, or whether a client would actually choose a particular organization.

## Outputs

The build writes:

- `provider_service_types.csv`
- `tract_service_type_accessibility.csv`
- `service_type_accessibility_summary.csv`

Each tract-service row includes nearest modeled travel time and the number of relevant locations reachable within 30, 45, and 60 minutes.
