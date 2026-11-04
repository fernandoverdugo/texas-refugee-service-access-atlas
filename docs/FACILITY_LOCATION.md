# Facility-location optimization

## Planning question

> If one additional refugee-service location could be added to the Dallas–Tarrant study area, which transit-connected tract would improve 45-minute accessibility for the largest currently underserved population?

The model is a **one-site maximum-coverage facility-location problem**.

## Candidate locations

Candidate sites are census-tract representative points that already have at least one modeled transit-stop connector within the project's one-kilometer walking threshold.

A candidate tract is therefore a planning location, not a recommended parcel or building.

The model does not evaluate:

- commercial real-estate availability
- rent or acquisition cost
- zoning
- agency ownership
- staffing
- program eligibility
- co-location opportunities
- political feasibility

Those would be required before any real site-selection decision.

## Objective

The default objective maximizes newly covered **foreign-born population** among tracts that currently have no verified refugee-service provider reachable within 45 modeled minutes.

Foreign-born population is used only as an aggregate planning context variable. It is **not** treated as a refugee population estimate.

For candidate site \(j\):

\[
\max_j \sum_i w_i a_{ij}(1-b_i)
\]

where:

- \(w_i\) is the foreign-born population in tract \(i\);
- \(a_{ij}=1\) when candidate \(j\) is reachable from tract \(i\) within 45 modeled minutes;
- \(b_i=1\) when tract \(i\) already has at least one existing provider reachable within 45 modeled minutes.

Because exactly one new site is selected, evaluating every candidate gives the exact optimum for this formulation.

## Tie-breaking

Candidates with equal foreign-born coverage are ranked by:

1. newly covered no-vehicle households;
2. newly covered total population;
3. tract GEOID for deterministic output.

## Interpretation

The result identifies the **best tract-level transit-access candidate under the model assumptions**. It should not be read as a recommendation to open a real facility at the tract representative point.

The purpose is to show how service-location planning could use accessibility data to identify areas worth deeper feasibility analysis.


## Equity-aware scenarios

The same 45-minute reachability matrix is re-scored under four objectives:

- foreign-born population
- total population
- households with no vehicle
- population below poverty

The candidate set, transit network, access threshold, and existing-provider baseline are held constant. Only the objective weight changes.

This makes the comparison interpretable: when the recommended tract changes, the change is caused by the planning objective rather than by a different network or candidate universe.

### Current result

Three objectives select Dallas County tract `48113003102`:

- foreign-born population
- total population
- no-vehicle households

The poverty-weighted objective selects Dallas County tract `48113008701`.

The result demonstrates that a site described as "optimal" is conditional on what the planner is trying to maximize. The project therefore presents the objective explicitly instead of hiding it inside a single recommendation.
