# GOES-19 2025 Temporal and Sensor Holdout Protocol

Frozen: 6 August 2026, before extraction or inspection of any 2025 GOES-19 land-surface-temperature outcome.

## Purpose

This analysis tests whether the cross-sunset urban core-minus-ring transition found with GOES-16 during 2018-2024 replicates in a new year and a different operational satellite. It is a temporal and sensor holdout. It does not reuse the pilot cities or select intervals from GOES outcomes.

## Frozen population

- Cities: the 184-city nonoverlapping GOES confirmation cohort frozen for the earlier study.
- Year: 2025 only.
- Satellite: GOES-19 ABI Level-2 Land Surface Temperature, full-disk product `ABI-L2-LSTC`.
- Spatial units: the same GHS urban-center core and 10-20 km surrounding ring used in the earlier confirmation.

## Outcome-independent interval census

Eligible intervals are all recurring 8-day intervals that:

1. start between 1 June and 31 August 2025;
2. contain at least 20 city observations exceeding the city- and step-specific true-night 2 m air-temperature P90; and
3. have a within-interval hydroclimatic-severity standard deviation of at least 10 percentile points among those hot city observations.

These rules use only ERA5-Land exposure variables. They yield ten consecutive intervals beginning 18 June through 29 August 2025 (steps 22-31). All ten are retained; no interval will be removed based on GOES outcomes.

## Frozen exposure and outcomes

Hydroclimatic severity is the mean of root-zone soil dryness percentile (`100 - soil-moisture percentile`) and vapor-pressure-deficit percentile. The primary exposure is severity per 10 percentile points among true-night heat city-intervals.

The primary outcome is the transition shift in the core-minus-ring GOES LST anomaly:

- pre-sunset anomaly: mean over target hours -3 to -1;
- late post-sunset anomaly: mean over target hours +4 to +6; and
- transition shift: late post-sunset minus pre-sunset anomaly.

Secondary outcomes are the hourly anomaly trajectory, the zero-crossing time of the adjusted dry-hot contrast, the six-hour post-sunset integrated excess, and separate core and ring cooling trajectories.

## Frozen quality rules

- Primary QA: GOES DQF = 0.
- Sensitivity QA: GOES DQF <= 1.
- Physically valid LST only.
- At least three valid core pixels and ten valid ring pixels per scan.
- At least two valid local dates per city-interval for the primary transition outcome.
- High-coverage sensitivity: at least four valid local dates.

## Primary model and inference

The primary model regresses transition shift on severity per 10 points among true-night heat observations, with city and interval fixed effects. The confirmatory test is two-sided and uses interval-level wild-cluster bootstrap inference. With ten intervals, all Rademacher sign patterns will be enumerated. City-and-interval clustered standard errors and a two-way city-by-interval bootstrap will be reported as supporting uncertainty estimates.

The 2025 result will be considered a successful independent confirmation only if the severity coefficient is positive and the interval-level wild-bootstrap two-sided P value is below 0.05. Effect magnitude and uncertainty will be reported regardless of the result.

## Pre-specified supporting analyses

1. Adjustment for actual true-night 2 m air temperature, pre-sunset core LST, and pre-sunset ring LST.
2. Separate soil-dryness and VPD terms, with true-night temperature included.
3. Strict versus recommended GOES QA and two- versus four-day support.
4. Hourly severe-minus-lower-severity trajectory for the subset of intervals containing both groups.
5. Clear-sky retention by hour and hydroclimatic state.
6. Leave-one-interval-out influence analysis.

No 2025 GOES outcome will be used to redefine the city set, interval set, exposure thresholds, time windows, or primary outcome.
