# Exploratory Thermal-Disequilibrium Analysis Protocol

Frozen: 7 August 2026, after the frozen 2025 transition-shift test failed and
before formal inference for the thermal-disequilibrium outcomes was run.

## Purpose

This analysis tests whether the observed pre- to post-sunset temperature change
is primarily explained by the initial surface-to-air temperature excess, and
whether hydroclimatic severity contributes information beyond that physical
boundary condition. It is exploratory and cannot replace the failed 2025
confirmatory test.

## Samples

1. GOES-16, 2018-2024, all 73 outcome-independent eligible intervals.
2. GOES-16, 2018-2024, the 61 intervals not used in the original selected-event
   analysis.
3. GOES-19, frozen 2025 temporal and sensor holdout.
4. GOES-18, frozen 2025 western-domain sensor replication.

The strict `DQF = 0` sample is primary. Observations must satisfy the frozen
city-specific true-night heat criterion and contribute at least two valid days
to both the pre-sunset (-3 to -1 h) and late-post-sunset (+4 to +6 h) windows.

## Outcomes and models

For the core and surrounding ring separately, the window temperature change is
late-post-sunset LST minus pre-sunset LST. The initial thermal excess is
pre-sunset LST minus mean true-night 2-m air temperature. A finite-window
thermal-release fraction is the negative temperature change divided by the
initial thermal excess. Release-fraction analyses require an initial excess
greater than 2 K and exclude fractions outside -1 to 2.

City and interval fixed-effects models estimate:

1. temperature change on hydroclimatic severity;
2. temperature change on severity, true-night air temperature and the initial
   surface temperature;
3. thermal-release fraction on severity; and
4. the core-minus-ring release-fraction difference on severity.

Uncertainty is evaluated with two-way city and interval clustering and an
interval-level Rademacher wild bootstrap. Consistency across cohorts and sensors,
rather than significance in any one cohort, determines interpretation.

## Interpretation guardrail

The normalized release fraction is an observational proxy, not a material heat
capacity or causal energy-budget estimate. A severity association is considered
generalizable only if its sign is consistent in both the historical unseen-event
sample and the frozen 2025 holdout.
