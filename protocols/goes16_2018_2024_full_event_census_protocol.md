# GOES-16 2018-2024 Full Event Census Protocol

Frozen before extracting GOES outcomes for the 61 intervals not used in the original 12-interval analysis. This is a retrospective event-selection sensitivity analysis, not a prospective confirmation, because outcomes from the original 12 intervals were already known.

## Purpose

Test whether the original cross-sunset transition survives replacement of the selected 12-interval sample with every outcome-independent eligible warm-season interval.

## Population and event census

- Cities: the previously frozen 184-city nonoverlapping higher-vegetation-support confirmation cohort.
- Satellite: GOES-16 ABI Level-2 Land Surface Temperature, full-disk `ABI-L2-LSTC`.
- Years: 2018-2024.
- Season: intervals beginning in June, July or August.
- Eligibility: at least 20 city observations above the city- and step-specific true-night 2 m air-temperature P90 and a within-interval hydroclimatic-severity standard deviation of at least 10 percentile points.
- All eligible intervals are retained without reference to GOES outcomes.

The frozen census contains 73 intervals. Twelve were used previously; the remaining 61 provide an unobserved event expansion.

## Outcomes and inference

The primary exposure, transition-shift outcome, quality rules and event-aware inference follow the GOES-19 temporal-and-sensor holdout protocol. The principal analysis uses DQF = 0, at least three core pixels and ten ring pixels per scan, at least two valid dates per city-interval, city and interval fixed effects, and interval-clustered inference. Because 73 intervals preclude exact enumeration of all sign patterns, a reproducibly seeded interval-level wild bootstrap with at least 9,999 draws will be used.

Results will be reported for all 73 intervals and separately for the 61 intervals outside the original selected set. Event-level and year-level heterogeneity will be retained whether or not the aggregate coefficient is positive.
