# Frozen expanded-population validation protocol

Frozen on 2026-08-10 before extracting any GOES-18 observation for the expansion cohort.

## Purpose

Evaluate whether results from the preregistered 44-city harmonization experiment generalize to western cities that were not used in model derivation or initial validation. The expansion cohort consists of all cities in the previously defined lower-vegetation-support comparison set with longitude at or west of 100 degrees W. Selection uses metadata only and does not inspect GOES-18 outcomes.

## Samples

- Spatial replication: paired GOES-18/GOES-16 observations in 2022-2024 for the expansion cities and the same 31 calendar intervals used in derivation.
- External spatial/platform replication: paired GOES-18/GOES-19 observations in 2025 for the expansion cities and the same ten calendar intervals used in the initial 2025 validation.
- Exact-pair, quality, scan-time, aggregation and transition rules are unchanged from `MULTIPLATFORM_HARMONIZATION_PROTOCOL.md`.

## Frozen model

The selected ten-hour additive correction in `frozen_harmonization_model.joblib` is applied without refitting. The expansion data cannot be used to select predictors, tune parameters or modify correction values for the primary analysis.

## Primary questions

1. Does the frozen correction reduce 2025 hourly core-minus-ring anomaly RMSE by at least 10% in previously unobserved cities?
2. Does it reduce absolute mean core-minus-ring transition bias by at least 50%?
3. Does event-level core-minus-ring transition RMSE remain materially larger than the corrected core and ring component errors, confirming that component calibration does not guarantee interchangeability of a derived transition metric?
4. Are the directions of hourly and transition changes consistent between the original and expansion cohorts under leave-one-event-out analysis?

The transition-RMSE criterion from the original protocol remains reported. Failure to reduce transition RMSE is treated as a substantive limitation of hour-only harmonization rather than suppressed or redefined.

## Secondary analyses

- Combine original and expansion cities to describe the complete extracted western common-domain sample.
- Stratify metrics by longitude, view-zenith-angle quartile, city core-pixel support and the pre-existing vegetation-support cohort.
- Quantify the error cascade from absolute core/ring LST through core-minus-ring anomaly to pre-to-post-sunset transition.
- Apply the previously screened metric-aware models only as labeled secondary diagnostics; the derivation screening selected no transition correction.

## Claim boundary

The expansion tests empirical transfer across a broader set of western North American urban landscapes. It does not make the sample globally representative, identify the physical cause of directional anisotropy or validate the correction outside the GOES-East/GOES-West platform slots and tested clear-sky product.
