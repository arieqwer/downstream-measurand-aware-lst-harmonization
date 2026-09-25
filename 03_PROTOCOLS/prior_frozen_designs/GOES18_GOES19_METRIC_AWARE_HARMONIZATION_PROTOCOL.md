# Frozen GOES-18/GOES-19 metric-aware harmonization protocol

Frozen on 2026-08-10 before extracting either platform for the 2026 temporal holdout.

## Motivation

The zero-shot GOES-16-derived hourly correction reduced absolute core and ring error in GOES-19 data but did not transfer consistently to the core-minus-ring anomaly or its sunset transition. This protocol therefore tests a sensor-pair-specific and metric-aware strategy, trained during GOES-18/GOES-19 overlap in 2025 and evaluated once in independent 2026 intervals.

## Calibration and holdout samples

- Calibration: all exact GOES-18/GOES-19 pairs already extracted for the original and expansion western cohorts in ten 2025 intervals.
- Temporal holdout: all metadata-eligible cities from both cohorts at longitude at or west of 100 degrees W, observed during eight fixed eight-day windows from 1 June through 3 August 2026.
- The 2026 dates and city list are fixed without inspecting any 2026 LST outcome.
- Recommended-quality core and ring values, at least 3 and 10 valid pixels respectively, and no more than 15 minutes absolute scan-time separation are required.

## Metric-aware outcomes

Models are evaluated at three levels:

1. absolute core and ring hourly LST;
2. hourly core-minus-ring LST anomaly, calibrated directly rather than inferred only by subtracting two corrected absolute temperatures; and
3. the core-minus-ring transition from hours -3 to -1 before sunset to hours +4 to +6 after sunset, calibrated directly at city-event level.

Direct calibration is used because a derived small spatial difference can retain structured residual error even when its two larger component temperatures are individually corrected.

## Candidate point models

All models use only quantities available from the eastern source platform and static geometry.

- `raw`: no correction.
- `hour_offset` or `mean_offset`: fixed additive correction.
- `geometry_ridge`: hour indicators plus latitude, longitude, source and target view-zenith angle, angle difference and angle mean.
- `scene_gbdt`: geometry plus source core, ring, mean-surface and core-minus-ring temperature and their sunset-relative timing.

No vegetation-support group, hydroclimatic severity, target-platform temperature, city identifier or 2026 information is a predictor.

## Calibration-only model selection

Cities are assigned to five longitude-ranked spatial blocks and the ten 2025 intervals to five chronological event blocks. Each of 25 crossed folds tests one spatial x event block and excludes every observation from either held-out block during fitting. Candidate selection uses RMSE and the one-standard-error rule, preferring models in the order listed above. A correction is not forced if raw observations are within one standard error of the best model.

Separate candidates are selected for core, ring, direct hourly anomaly and direct transition. The final selected models are fitted once to all 2025 calibration observations and serialized before 2026 extraction.

## Uncertainty gate

Absolute residuals from crossed out-of-fold predictions of the selected direct-transition model define a fixed 90th-percentile uncertainty half-width. The 2026 prediction interval is the point estimate plus or minus this frozen half-width. This is reported as grouped out-of-fold uncertainty calibration, not as an assumption-free conformal guarantee because city-events share event conditions.

A transition direction is certified only when the entire interval lies above or below zero. The method may abstain when platform uncertainty is too large relative to the derived signal.

## Prospective success criteria

The 2026 method is considered practically successful if:

1. direct hourly anomaly RMSE decreases by at least 15%;
2. direct transition RMSE decreases by at least 10%, or, if point improvement is smaller, the uncertainty interval attains 85-95% pooled coverage with at least 90% accuracy among sign-certified transitions;
3. core and ring hourly RMSE each decrease by at least 30%;
4. improvements do not reverse under any leave-one-event-out omission for the primary hourly anomaly result; and
5. all metrics are reported for both pre-existing cohorts and the combined sample.

## Claim boundary

Successful validation supports a practical empirical calibration for GOES-18/GOES-19 clear-sky urban sunset observations in the tested common domain. It does not identify a universal physical angular law, guarantee performance for other satellites or products, or make uncertified transition signs interchangeable across platforms.
