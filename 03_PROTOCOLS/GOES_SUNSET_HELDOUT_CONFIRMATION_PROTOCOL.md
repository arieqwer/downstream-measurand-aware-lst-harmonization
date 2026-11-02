# GOES sunset held-out confirmation protocol

Frozen: 6 August 2026, after the 60-city pilot and before GOES outcomes were
extracted for the held-out cities.

## Cohort

- All 184 eligible high-green-support cities in the GOES-16 CONUS domain that
  were absent from the 60-city pilot and had complete water-support and urban-
  structure predictors.
- The same twelve 8-day intervals selected without GOES outcome data for the
  pilot.
- The same hourly window, geometries, quality rules, outcomes, thresholds, and
  two-day city-event requirement as the original protocol.

## Primary confirmation targets

1. Severe-hot minus lower-severity-hot difference in the post-sunset
   core-minus-ring LST slope.
2. Severe-hot minus lower-severity-hot difference in the pre-to-late-night
   core-minus-ring LST shift.
3. Continuous hydroclimatic-severity coefficient for both outcomes under city
   and interval fixed effects.

## Mechanistic decomposition added after the pilot

The pilot indicated an unexpected differential mechanism: both core and ring
cooled faster during severe-hot intervals, but the ring accelerated more, so the
relative core excess dissipated more slowly. Before opening the held-out GOES
outcomes, we therefore specify separate core and ring post-sunset slopes as a
secondary confirmation test. Support requires severe-hot conditions to make both
slopes more negative, with a larger-magnitude change in the ring than in the core.
Sunset-normalized core and ring trajectories will visualize this decomposition.

Strict DQF = 0 results are primary. DQF <= 1 results are sensitivity estimates.
The direction must be positive in the pooled held-out cohort and in both the
2018-2021 and 2022-2024 temporal subsets to claim temporal confirmation.

Because cities share only twelve event intervals, primary fixed-effect
uncertainty is clustered by both city and interval, with inference degrees of
freedom based on the smaller cluster dimension. City-only clustered estimates
are retained as a sensitivity analysis.

## Falsification and scope

- The pre-sunset core-minus-ring slope is the negative-time control when enough
  valid observations are available.
- A high-coverage sensitivity requires at least four valid days per 8-day
  city-event for the same fixed-effect outcomes, reducing concern that clearer
  dry events receive systematically denser hourly sampling.
- Water-support and built-intensity interactions are secondary mechanism tests.
  The 60-city pilot did not establish a temporally replicating built modifier;
  it will not be claimed unless the held-out cohort supplies consistent evidence.
- The result is a clear-sky surface-temperature transition, not a direct measure
  of heat storage flux, 2-m air temperature, or causal intervention effects.
