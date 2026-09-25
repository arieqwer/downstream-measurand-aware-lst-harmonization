# Frozen GOES-17/GOES-16 external metric-replication protocol

Frozen on 2026-08-10 before listing or extracting any GOES-17 LST file for this analysis.

## Purpose

This optional external test asks whether the component-improvement and covariance-loss pattern occurs for an earlier, independent GOES-West/GOES-East platform pairing. It is a fixed diagnostic replication, not a new model search.

## Cities and periods

- City population: the 75 cities fixed for the GOES-18/GOES-19 metric-aware analysis, restricted only by the same minimum grid support on both GOES-16 and GOES-17.
- Calibration windows: eight-day intervals starting 1 June and 17 July in 2019 and 2020.
- External validation windows: eight-day intervals starting 1 June, 17 June, 3 July and 19 July 2021.
- Dates are calendar-fixed and were chosen without GOES-17 outcome inspection.
- Hours: integer target hours -3 through +6 relative to local sunset.
- Exact-platform pair requirements: shared city, date and target hour, no more than 15 minutes absolute scan-time separation, at least two paired days per city-interval-hour, at least three recommended-quality core pixels and ten recommended-quality ring pixels.

## Fixed correction

Estimate separate hour-from-sunset mean additive corrections for core and ring from the four 2019-2020 calibration intervals. Apply them without refitting to the four 2021 validation intervals.

No viewing-geometry model, spline, machine-learning model, alternative date set or subgroup-specific correction will be tested.

## Primary external diagnostic

In the 2021 validation sample, compute the exact downstream hourly MSE budget defined in `DOWNSTREAM_METRIC_AWARE_HARMONIZATION_PROTOCOL.md`.

The external pattern is considered replicated if:

1. core and ring RMSE both improve after the fixed correction;
2. core-ring error covariance declines; and
3. downstream anomaly MSE gain is smaller than the summed component variance and differential-bias gains because `P_covariance` is positive.

The downstream anomaly need not worsen. The test concerns whether covariance loss explains attenuation between upstream and downstream improvement.

Transition-level results are secondary because only four independent 2021 validation intervals are available.

## Inference and reporting

- Report point estimates and 5,000 crossed city-event bootstrap draws.
- Report all results regardless of direction.
- Do not alter the already validated 2025-2026 models or claim that this historical pair is a prospective holdout.
- If archive availability, grid support or paired coverage is inadequate, report the failed feasibility test rather than changing dates.

