# Baseline-Adjusted Cross-Sunset Transition Protocol

Frozen: 7 August 2026, before estimating this model.

## Motivation

The change-score outcome subtracts the pre-sunset core-minus-ring anomaly and
can therefore be sensitive to baseline imbalance or regression to the mean.
This diagnostic estimates the late-post-sunset anomaly directly while
conditioning on the corresponding pre-sunset thermal state.

## Frozen model

For each strict-quality city-event observation, the outcome is mean core-minus-
ring LST at hours +4 to +6 relative to sunset. The focal predictor is continuous
hydroclimatic severity per 10 percentile points. Covariates are:

- mean core-minus-ring LST at hours -3 to -1;
- mean core-and-ring pre-sunset surface temperature; and
- true-night 2-m air temperature.

All models include city and event fixed effects. Inference for the severity
coefficient uses interval-level Rademacher wild-bootstrap tests.

## Cohorts and decision rule

The frozen cohorts are GOES-16 2018-2024, the previously unseen 61 historical
intervals, GOES-18 2022-2024, GOES-19 2025, and GOES-18 western 2025. A general
baseline-independent transition is eligible for interpretation only if the
severity coefficient is positive in every cohort and supported in both the
historical and independent 2025 periods. Otherwise, the result is reported as
temporally or platform contingent.
