# Frozen cross-platform harmonization protocol

Frozen on 2026-08-10 before fitting any harmonization model or inspecting any corrected 2025 result.

## Objective

Test whether a correction learned only from paired GOES-18/GOES-16 observations in 2022-2024 transfers, without refitting, to paired GOES-18/GOES-19 observations in 2025. GOES-18 is the target scale and the eastern platform is the source to be harmonized.

This experiment addresses a measurement question: can a parsimonious, sunset-relative calibration reduce platform-dependent error in urban core, surrounding-ring, and core-minus-ring land-surface-temperature trajectories and their pre-to-post-sunset transition metrics?

## Frozen samples

- Derivation: exact paired GOES-18/GOES-16 observations from 2022-2024.
- External temporal/platform validation: exact paired GOES-18/GOES-19 observations from 2025.
- Recommended-quality pixels from both platforms, absolute scan-time separation no greater than 15 minutes, and valid core and ring observations on both platforms.
- Hourly records are averaged within city x event interval x target hour before model fitting. Each city-event-hour therefore receives equal weight regardless of the number of clear-sky days contributing to the 8-day interval.
- The validation data may be read only after the derivation model has been selected and serialized.

## Outcomes

Separate corrections are fitted for core and ring LST. Corrected source values are calculated as source LST plus predicted target-minus-source bias. The corrected core-minus-ring anomaly is derived from the two corrected components, preserving internal consistency.

Primary validation outcomes:

1. RMSE of the hourly core-minus-ring anomaly.
2. RMSE of the city-event transition, defined as mean anomaly at hours +4 to +6 minus mean anomaly at hours -3 to -1.
3. Absolute mean bias of that transition.

Secondary outcomes:

- hourly core and ring mean bias, MAE, RMSE, and Lin concordance correlation;
- hourly anomaly mean bias, MAE, RMSE, and concordance;
- core, ring, and anomaly transition MAE and RMSE;
- disagreement between target and source in the sign of the anomaly transition;
- event-level and leave-one-event-out stability;
- attenuation of the previously observed mixed-platform temporal interaction when the historical eastern record is harmonized to the GOES-18 scale.

## Candidate models

All models predict GOES-18 minus eastern-platform bias separately for core and ring.

1. `raw`: no correction.
2. `hour_offset`: ten fixed offsets for integer hours -3 through +6.
3. `hour_spline`: cubic spline of target hour with five knots and ridge regularization.
4. `geometry_ridge`: cubic hour spline plus latitude, longitude, eastern and western view-zenith angles, their difference and mean, and linear hour-by-geometry interactions, with ridge regularization.

No city identifier, event identifier, year indicator, hydroclimatic state, vegetation measure, or validation-period information is allowed as a predictor.

## Derivation-only model selection

Candidate models are evaluated with crossed temporal-spatial blocking. Cities are assigned to five fixed longitude-ranked blocks. For each of 15 folds, one year and one spatial block form the test slice; all observations from that year or that spatial block are excluded from training. This requires prediction for both an unseen year and unseen cities.

For each candidate, core and ring models are fitted within each fold, then anomaly and transition predictions are reconstructed. Transition metrics require at least two observed target hours in each of the pre-sunset (-3 to -1) and late-post-sunset (+4 to +6) windows. Selection uses the mean of normalized cross-validated RMSE for hourly core, ring, and anomaly plus transition core, ring, and anomaly. The denominator for each component is the corresponding raw RMSE. The simplest model within one cross-fold standard error of the lowest composite score is selected in this fixed order: `raw`, `hour_offset`, `hour_spline`, `geometry_ridge`. Thus, the protocol does not force selection of a correction when the derivation data do not support one.

After selection, the chosen model is fitted once to all 2022-2024 derivation data and serialized. Only then is it applied unchanged to 2025.

## Prospective success criteria

The frozen model is considered to provide useful external harmonization only if all of the following hold in 2025:

1. hourly anomaly RMSE falls by at least 10% relative to the raw eastern platform;
2. anomaly-transition RMSE falls by at least 10%;
3. the absolute mean anomaly-transition bias falls by at least 50%; and
4. transition-sign disagreement does not worsen by more than 5 percentage points.

The method is considered strongly transferable if hourly and transition RMSE both fall by at least 20% and the direction of improvement remains under every leave-one-event-out omission.

## Uncertainty and non-independence

Validation uncertainty is summarized by a crossed city/event bootstrap and by leave-one-event-out estimates. Because only nine 2025 event intervals are available, event-level estimates and ranges are reported alongside pooled metrics; city-hour counts are not treated as independent temporal replications.

## Sample expansion

The frozen test uses the already extracted common-support sample and does not redefine it after seeing validation results. A subsequent generalization analysis may add all eligible western cities observed by both platforms, including lower-vegetation-support cities, but it must retain this frozen correction without refitting for the primary expanded validation. Any newly fitted all-city model is exploratory and reported separately.

## Frozen input hashes

- GOES-18 2022-2024 hourly analysis: `116c57f0e896124c5fcc0091ed71503094ded0c4c95ecd26522944311ba852a5`
- GOES-16 2022-2024 hourly analysis: `06b5ca1b44ab30359398b080039769261bad14e5fabb56d801e2fbb1b6f03f12`
- GOES-18 2025 hourly analysis: `8b1bc3dff7813a60e080ec3fe953ce6eb37e56275a28ec9f9b384e86a17b32ba`
- GOES-19 2025 hourly analysis: `a50ad5472518323d33feed51f4bbc397658605ae4d94b4c62fe548045be75c15`
- Frozen western-city metadata: `771aa2059cb38371d1ee05cbde1f23216ef42834e2c3250730285ac792bd3219`

## Claim boundary

Success supports transferable empirical harmonization for the tested GOES platform slots, urban sample, clear-sky quality screen, and sunset-relative metric. It does not establish a universal physical angular correction, interchangeability for all LST applications, or a causal explanation for the platform offset.
