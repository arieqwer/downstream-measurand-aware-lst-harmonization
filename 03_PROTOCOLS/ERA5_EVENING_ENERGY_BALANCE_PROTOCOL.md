# ERA5 Evening Energy-Balance Constraint Protocol

Frozen: 7 August 2026, before extraction or inspection of the ERA5 evening
energy-balance covariates defined below.

## Purpose

The frozen 2025 GOES-19 transition-shift test did not replicate the historical
GOES-16 estimate. This analysis tests one physically specified explanation for
that temporal heterogeneity: whether radiative and turbulent boundary conditions
modify the association between hydroclimatic severity and the core-minus-ring
temperature transition.

## Data and population

- ERA5 hourly single-level fields in Google Earth Engine
  (`ECMWF/ERA5/HOURLY`).
- Every retained Northern American city in the frozen higher- and
  lower-vegetation-support cohorts.
- All 73 outcome-independent 2018-2024 census intervals and the ten frozen 2025
  intervals.
- ERA5 values are sampled at each urban-center centroid. They describe the
  background atmosphere and do not resolve core-minus-ring meteorological
  differences.

## Local-solar-time windows

Longitude is converted to the nearest integer solar UTC offset. For every local
date in each 8-day interval, the pre-evening window contains 15:00-18:59 local
solar time and the post-sunset window contains 21:00-02:59 local solar time.
Exact UTC timestamps are generated from the local dates and offset; no outcome
data enter timestamp selection.

## Frozen covariates

The extracted fields are 2-m temperature, 2-m dew-point temperature, 10-m wind
speed, total cloud cover, downward longwave radiation, downward shortwave
radiation, net longwave radiation, net shortwave radiation and boundary-layer
height. Hourly mean-rate radiation bands are used where available.

## Hypotheses and inference

The outcome remains the strict-QA pre- to late-post-sunset core-minus-ring
transition shift. Models include city and interval fixed effects, actual
true-night 2-m temperature and pre-sunset mean surface temperature.

Three moderators are tested separately to avoid an unconstrained model search:

1. post-sunset downward longwave radiation;
2. post-sunset 10-m wind speed; and
3. post-sunset total cloud cover.

The physical expectation is that stronger atmospheric radiative coupling,
greater cloud cover and greater turbulent mixing weaken differential clear-sky
surface cooling, producing negative severity-by-moderator interactions. Each
interaction must retain its sign in 2018-2021, 2022-2024 and 2025 to be described
as temporally generalizable. Interval-level wild-bootstrap inference is primary.

## Guardrails

This is an observational effect-modification test, not causal attribution or a
surface energy closure. A non-replicating interaction will be reported as a
failed mechanistic hypothesis and will not be replaced by an outcome-selected
moderator.
