# Reproducibility protocol

This document preserves the fixed protocols, analytical parameters, and computational specifications used for the study. It describes the processed-data workflow represented in this reviewer repository; raw provider files are not redistributed.

## Study cohorts and frozen chronology

At each stage, one Advanced Baseline Imager (ABI) platform defined the inter-platform consistency scale and a source platform was mapped to it. GOES-18 was the reference for GOES-18/GOES-16 comparisons in 2022–2024 and GOES-18/GOES-19 comparisons in 2025–2026. GOES-17 was the reference for the historical GOES-17/GOES-16 comparison in 2019–2021. Corrections estimated reference-minus-source discrepancy and added it to the source observation.

The western candidate population contained 94 non-overlapping cities at or west of 100°W: 51 cities in the pre-existing original cohort and 43 in the metadata-defined expansion cohort. The frozen candidate extent was 32.0051–49.8854°N and 123.9869–101.8614°W. Pairing and support retained 44 original and 31 expansion cities, yielding a 75-city common-support population with an analyzed extent of 32.2324–49.2333°N and 123.3533–104.7147°W. The same 75 cities formed the external-replication candidate population; 69 contributed retained hourly observations in both its calibration and validation periods.

- The initial correction used 44 original-cohort cities and 31 fixed eight-day intervals in 2022–2024. The 31 retained expansion cities on the same dates were excluded from fitting and provided a spatial-transfer evaluation.
- The frozen initial correction was applied without refitting to the original and expansion cohorts across ten fixed 2025 intervals. These cohorts were out of sample for the initial correction. Their combined 75-city data then calibrated the sensor-pair-specific GOES-18/GOES-19 selector.
- The 2026 candidate list and eight calendar windows were frozen before either platform was extracted. Model identities, predictor sets, selected actions, residual half-width, and decision criteria were fixed from the 2025 calibration before the holdout was opened.
- The historical external replication used four calendar-fixed 2019–2020 intervals for calibration and four calendar-fixed 2021 intervals for validation. The design was frozen before any GOES-17 file was listed or extracted.

The five headline out-of-sample cohorts were the 2021 external cohort, 2022–2024 expansion cohort, 2025 original cohort, 2025 expansion cohort, and combined 2026 holdout. Cohorts sharing calendar intervals were not treated as independent temporal replications. All dates were inclusive eight-day windows. The main designs comprised 31 intervals from 10 June 2022 through 4 September 2024; ten 2025 intervals beginning 18 June through 29 August; and eight 2026 intervals beginning 1 June through 27 July. The complete 57-row chronology, event identifiers, platform roles, source protocols, and frozen status are in `02_EVIDENCE/si_tables/fixed_interval_chronology.csv`.

## Inherited hydroclimatic event-selection protocol

Interval eligibility came from the processed 2003–2025 ERA5-Land city–interval panel.

- **True-night temperature:** the urban-core mean of hourly `temperature_2m` from `ECMWF/ERA5_LAND/HOURLY` for pixelwise local-solar hours from 22:00 through before 06:00. Values were averaged within each eight-day step and converted to degrees Celsius. Average-tie empirical percentile ranks were calculated within each city across all recurring steps; ranks of at least 90 were classified as hot.
- **Root-zone soil moisture:** the unweighted mean of `volumetric_soil_water_layer_1`, `volumetric_soil_water_layer_2`, `volumetric_soil_water_layer_3`, and `volumetric_soil_water_layer_4` from `ECMWF/ERA5_LAND/DAILY_AGGR`.
- **Vapor-pressure deficit (VPD):** calculated from 2-m temperature and dew-point temperature as

  \[
  \operatorname{VPD}=e_s(T)-e_s(T_d), \qquad e_s(T)=0.6108\exp\left[\frac{17.27T}{T+237.3}\right]\ \mathrm{kPa}.
  \]

- **Percentiles and severity:** average-tie percentiles of root-zone soil moisture and VPD were calculated within city and recurring eight-day step over 2003–2025. Hydroclimatic severity was the mean of 100 minus the root-zone soil-moisture percentile and the VPD percentile. Daily hydroclimatic fields were aggregated as five-day pentad means and assigned to an eight-day interval using the pentad containing its start date.
- **2022–2024 eligibility:** every recurring June–August eight-day interval with at least 20 hot city observations and an interval-level hydroclimatic-severity standard deviation of at least 10 percentile points across all candidate-city observations was retained. All 31 eligible intervals were used.
- **2025 eligibility:** the corresponding ERA5-Land-only heat and severity rules were applied to recurring June–August windows, with severity dispersion calculated among hot city observations. All ten eligible intervals were retained.

These selections did not use evaluated GOES outcomes, cross-platform discrepancies, or harmonization results. The 2026 holdout instead used eight consecutive windows generated before extraction. The 2019–2021 dates were separately calendar-fixed before GOES-17 file listing; archived records do not document a hydroclimatic selection rule or more specific rationale for them.

## ABI LST extraction, DQF rules, spatial geometry, minimum grid support, sunset alignment, exact platform pairing, and aggregation

The satellite input was the ABI Level-2 Land Surface Temperature CONUS-sector product (`ABI-L2-LSTC`) from the public NOAA GOES object archives. Packed `LST` was decoded with each file's scale factor and offset, with unsigned handling before fill-value removal. Eligible observations were finite, between 180 and 380 K, and had good- or medium-quality retrieval flags (DQF 0–1), where DQF 0 denotes good quality and DQF 1 medium quality. GOES-19 ABI L2 LST was at the Provisional maturity level during the 2025–2026 period.

Urban cores were fixed GHS Urban Centre Database R2024A polygons simplified with 250-m tolerance. The surrounding ring was the area between 10- and 20-km outward buffers constructed with the same maximum-error tolerance. Means used ABI grid-cell centers within each geometry. A platform-specific city mask required at least three core and ten ring grid cells. Of the 94 fixed 2026 candidates, 88 met this mask rule on GOES-18, 83 on GOES-19, and 78 on both; exact-pair coverage retained 75 cities. Candidate and support metadata are in `02_EVIDENCE/si_tables/fixed_city_candidate_metadata.csv`, and the auxiliary name lookup is `04_PROTOCOLS/frozen_inputs/AUXILIARY_UCDB_94_CITY_LOOKUP.csv`.

Astronomical sunset was calculated for every city and local date from the frozen coordinate with Astral 3.2 and converted to UTC. The trajectory contained ten target hours from −3 through +6. The requested time was sunset plus the target offset, rounded to the nearest UTC hour. Cross-platform daily observations were inner-joined on urban-center identifier, event year, eight-day step, event identifier, local date, and target hour. Both observations had to pass their spatial-quality rules, and acquisition times could differ by no more than 15 minutes. Retained values were averaged by city, interval, and target hour, and each city–interval–hour row received equal weight. The external GOES-17/GOES-16 replication additionally required at least two paired local dates per retained row. Object keys, acquisition times, and scan-time offsets were retained.

Satellite subpoint longitude, latitude, and perspective height came from representative native-file projection metadata. Reference and source view-zenith angles, their difference, and their mean were calculated from those metadata and city coordinates.

For each retained row, the spatial measurand was \(D=C-R\). The pre-sunset contrast was the mean at −3, −2, and −1 hours, and the post-sunset contrast was the mean at +4, +5, and +6 hours; each window required at least two retained hours. The temporal measurand was \(T=D_{\mathrm{post}}-D_{\mathrm{pre}}\). Source data retain `anomaly` as the historical field name for \(D\).

## Initial GOES-18/16 model candidates, predictors, settings, folds, and selection

The initial stage predicted GOES-18-minus-GOES-16 discrepancy separately for core and ring using four candidates:

- `raw`: no change to GOES-16;
- `hour_offset`: ten additive means, one for each sunset-relative hour;
- `hour_spline`: `SplineTransformer(n_knots=5, degree=3, include_bias=True)` applied to sunset-relative hour, followed by `RidgeCV`;
- `geometry_ridge`: `StandardScaler` followed by `RidgeCV`, using sunset-relative hour, latitude, longitude, reference and source view-zenith angles, angle difference, angle mean, and linear hour-by-geometry interactions.

Every ridge candidate used `RidgeCV` with 24 logarithmically spaced penalties from 10⁻³ through 10⁴ (`np.logspace(-3, 4, 24)`). City identifier, event identifier, year, hydroclimatic variables, vegetation measures, and validation-period information were excluded.

Cities were assigned deterministically to five longitude-ranked blocks. The 15 folds crossed three held years with five spatial blocks. Each test slice was the intersection of one held year and one held block, and training excluded every observation in either held group. Separate core and ring models were fitted in each fold, after which hourly and transition core, ring, and contrast predictions were reconstructed.

The fold score was the mean of six RMSE values divided by the corresponding raw RMSE: hourly and transition core, ring, and contrast. The one-standard-error cutoff was the lowest mean score plus its cross-fold standard error. Candidates within the cutoff were ordered `raw`, `hour_offset`, `hour_spline`, and `geometry_ridge`. Although `hour_spline` had the lowest mean score, 0.5601, `hour_offset` had a score of 0.5602 and remained within the 0.5989 cutoff, so `hour_offset` was selected. Separate core and ring offsets were fitted to all 13,454 derivation rows and serialized before transfer evaluation.

## GOES-18/19 measurand-aware candidates, predictors, settings, selection, and frozen 2026 decisions

The combined 2025 calibration sample contained 75 cities, ten intervals, 7,143 city–interval–hour rows, and 733 transitions. Candidates were selected independently for hourly core, hourly ring, direct hourly contrast, and direct contrast transition.

The hourly candidates were `raw`, `hour_offset`, `geometry_ridge`, and `scene_gbdt`. `geometry_ridge` used ten one-hot hour indicators, latitude, longitude, reference and source view-zenith angle, their difference, and their mean; its pipeline applied `StandardScaler` followed by `RidgeCV` with the same 24-value penalty grid as the initial stage. `scene_gbdt` added source core, ring, mean-surface, and core–ring temperatures plus interactions of normalized sunset-relative hour with source mean-surface and contrast temperature. It used histogram gradient boosting with learning rate 0.04, 300 iterations, at most 15 leaves, minimum leaf size 35, L2 regularization 2.0, and random state 20260810.

Direct-transition candidates were `raw`, `mean_offset`, `transition_ridge`, and `transition_gbdt`. Fitted candidates used source contrast, core and ring transitions; source pre- and post-sunset contrast; source pre- and post-sunset mean surface temperature; location; and reference/source viewing geometry. `transition_ridge` applied `StandardScaler` followed by `RidgeCV` with the same 24-value penalty grid. `transition_gbdt` used learning rate 0.04, 250 iterations, at most 12 leaves, minimum leaf size 25, L2 regularization 2.0, and random state 20260810. No candidate used city identifier, event identifier, original/expansion cohort, hydroclimatic state, vegetation metadata, reference-platform temperature, or a 2026 outcome.

The 75 cities were divided into five longitude-ranked blocks and the ten intervals into five chronological blocks. Each of 25 folds tested one spatial-by-event-block intersection while training excluded every observation in either held block. Fold RMSE was normalized by the corresponding raw RMSE, so `raw` had a score of 1.0. The simplest candidate within one standard error of the lowest mean ratio was selected using the fixed hourly order `raw`, `hour_offset`, `geometry_ridge`, `scene_gbdt` and transition order `raw`, `mean_offset`, `transition_ridge`, `transition_gbdt`.

Frozen selections were `geometry_ridge` for core, `hour_offset` for ring, `raw` for direct hourly contrast, and `raw` for direct transition. The selected objects were serialized before 2026 extraction. The 90th percentile of absolute crossed out-of-fold residuals from the selected direct-transition candidate, using the higher observed order statistic, fixed the empirical residual half-width at 1.535818 K. The 2026 extraction used the fixed 94-city list and eight windows beginning 1 June through 27 July (collectively 1 June through 3 August). Prespecified support retained 75 cities, 5,744 hourly rows, and 588 transitions. No 2026 discrepancy or result selected a model, changed a hyperparameter, revised the population or windows, or recalibrated the interval.

## Exact MSE decomposition, population moments, raw retention, and sign-support decisions

For raw or component-harmonized quantities, let \(e_c=\widehat C-C^R\) and \(e_r=\widehat R-R^R\), with population means \(b_c\) and \(b_r\). The core–ring discrepancy has

\[
\operatorname{MSE}(D)=\operatorname{Var}(e_c)+\operatorname{Var}(e_r)-2\operatorname{Cov}(e_c,e_r)+(b_c-b_r)^2.
\]

Raw-to-harmonized downstream gain was

\[
G_D=\operatorname{MSE}_{\mathrm{raw}}(D)-\operatorname{MSE}_{\mathrm{harm}}(D)
=G_{\mathrm{variance}}+G_{\mathrm{bias}}-P_{\mathrm{covariance}},
\]

where

\[
G_{\mathrm{variance}}=[V_{c,\mathrm{raw}}-V_{c,\mathrm{harm}}]+[V_{r,\mathrm{raw}}-V_{r,\mathrm{harm}}],
\]

\[
G_{\mathrm{bias}}=(b_{c,\mathrm{raw}}-b_{r,\mathrm{raw}})^2-(b_{c,\mathrm{harm}}-b_{r,\mathrm{harm}})^2,
\]

\[
P_{\mathrm{covariance}}=2[\operatorname{Cov}_{\mathrm{raw}}(e_c,e_r)-\operatorname{Cov}_{\mathrm{harm}}(e_c,e_r)].
\]

Positive component-variance and differential-bias gains favor harmonization. A positive covariance-loss penalty offsets those gains because covariance that previously canceled under subtraction decreased. The same calculation was applied to component transitions. All variances and covariances used population moments (`ddof = 0`) in the fixed sample. For a general linear measurand \(M=w^\top X\), covariance matrix \(\Sigma\), and bias vector \(b\), the implementation used

\[
\operatorname{MSE}(M)=w^\top\Sigma w+(w^\top b)^2.
\]

The decomposition is an accounting identity and does not identify physical causes. For every observed and bootstrap calculation, the absolute difference between directly calculated MSE change and the sum of the decomposition terms had to be below 1 × 10⁻¹⁰ K².

Actions were assigned at the measurand used for inference. Component correction was available when held-out component loss improved. A direct correction for \(D\) or \(T\) was available only when calibration selected it using that measurand's loss. Selection of `raw` meant raw retention even if the components were corrected. The residual interval supported a positive or negative transition sign only when it lay entirely above or below zero; otherwise the rule abstained. This interval is empirical cross-platform residual uncertainty, not a metrological expanded uncertainty interval.

## Crossed city–event bootstrap, event-influence analysis, deterministic covariance-regime grid, seed, and closure checks

Observed estimates used all retained rows in each fixed sample. The 2026 decomposition and 2021 external summaries used 5,000 crossed city–event bootstrap draws. Cities and eight-day events were sampled independently with replacement, and each row's weight was the product of the sampled multiplicities of its city and event. Weighted population moments and the full decomposition were recomputed for hourly and transition scopes. Reported 95% intervals are the empirical 2.5th and 97.5th percentiles. Observed point estimates remain primary; bootstrap means are computational diagnostics. Draw-level outputs are `02_EVIDENCE/bootstrap/mse_budget_2026_crossed_bootstrap.parquet` and `02_EVIDENCE/bootstrap/validation_2021_crossed_bootstrap.parquet`.

For the four-event external validation, every event was analyzed separately and the pooled hourly calculation was repeated four times after omitting one event. These were descriptive stability checks and did not create independent validation years. Outputs are in `02_EVIDENCE/external_replication/validation_2021_event_influence.csv`.

The frozen 2026 residual interval was the raw direct-transition estimate plus or minus 1.535818 K. Coverage indicated whether the GOES-18 transition was in the interval. An interval entirely above or below zero supported its sign. The fallback criterion required pooled coverage from 85–95% and at least 90% reference-sign agreement among supported signs when direct-transition RMSE did not improve by 10%. The combined sample was the formal decision scope; cohort and event summaries were transport diagnostics.

The deterministic stress test enumerated raw and harmonized core/ring residual correlations from 0 to 0.95 in increments of 0.01; raw core-to-ring residual-standard-deviation ratios of 0.85, 0.95, 1.05, 1.15, and 1.25; separate harmonized-to-raw component ratios from 0.45 through 0.95 in increments of 0.10; and standardized differential-bias-squared gains from −0.15 through 0.15 in increments of 0.05. Mean raw component variance was one. The grid contained 9,216 correlation cells, 1,260 nuisance configurations per cell, and 11,612,160 exact configurations. It used no random sampling, fitted model, or new satellite observation.

All stochastic model fitting and resampling used integer seed 20260810. Numerical validation required observed and bootstrap MSE closure below 1 × 10⁻¹⁰ K², and unit tests independently covered exact closure.

## Historical GOES-17/16 replication

The external protocol was frozen on 10 August 2026 before any GOES-17 LST file was listed or extracted. Its candidate population was the 75-city common-support set, subject to the same minimum support on GOES-16 and GOES-17. Calibration windows began 1 June and 17 July in both 2019 and 2020. Validation windows began 1 June, 17 June, 3 July, and 19 July 2021.

The design fixed all ten target hours, a 15-minute maximum scan separation, DQF 0–1 retrievals, the 180–380 K range, minimum support of three core and ten ring pixels, and at least two paired days per city–interval–hour. Separate GOES-17-minus-GOES-16 mean offsets were estimated for core and ring at each sunset-relative hour from the four calibration events and added unchanged to 2021 GOES-16 values. The offsets are in `02_EVIDENCE/external_replication/frozen_hour_offsets_2019_2020.csv` and `02_EVIDENCE/si_tables/external_hour_offsets_2019_2020.csv`.

No geometry model, spline, machine-learning candidate, alternative calendar, subgroup model, or validation-year refit was evaluated. The primary diagnostic required improved 2021 core and ring RMSE, declining core–ring residual covariance, and a positive covariance-loss penalty that attenuated downstream gain relative to component-variance plus differential-bias gain. Downstream deterioration was not required, and transition results were secondary because only four validation events were available. All observed and bootstrap results were retained regardless of direction.

## Software versions, frozen manifests, source hashes, tests, builds, validation, and repository paths

Principal analyses used Python 3.9.6, NumPy 2.0.2, pandas 2.3.3, Matplotlib 3.9.4, PyArrow 21.0.0, and scikit-learn 1.6.1. Complete dependencies are in `05_CODE/requirements_goes.txt`. Spatial and event blocks were deterministic functions of longitude rank and chronological event order.

The principal frozen protocols and reconstruction guides are:

- `04_PROTOCOLS/DOWNSTREAM_METRIC_AWARE_HARMONIZATION_PROTOCOL.md`
- `04_PROTOCOLS/GOES17_GOES16_EXTERNAL_METRIC_REPLICATION_PROTOCOL.md`
- `04_PROTOCOLS/DOWNSTREAM_METRIC_FRAMEWORK_REPRODUCIBILITY.md`
- `04_PROTOCOLS/prior_frozen_designs/METRIC_HARMONIZATION_REPRODUCIBILITY.md`

Principal selection and fitted-model manifests are preserved under `04_PROTOCOLS/frozen_inputs/`, including:

- `04_PROTOCOLS/frozen_inputs/INITIAL_HARMONIZATION_FROZEN_MANIFEST.json`
- `04_PROTOCOLS/frozen_inputs/METRIC_AWARE_HARMONIZATION_FROZEN_MANIFEST.json`
- `04_PROTOCOLS/frozen_inputs/GOES18_2022_2024_ORIGINAL_FROZEN_SELECTION.json`
- `04_PROTOCOLS/frozen_inputs/GOES18_2022_2024_EXPANSION_FROZEN_SELECTION.json`
- `04_PROTOCOLS/frozen_inputs/GOES18_2025_ORIGINAL_FROZEN_SELECTION.json`
- `04_PROTOCOLS/frozen_inputs/GOES18_2025_EXPANSION_FROZEN_SELECTION.json`
- `04_PROTOCOLS/frozen_inputs/GOES18_2026_FROZEN_SELECTION.json`
- `04_PROTOCOLS/frozen_inputs/GOES19_2026_FROZEN_SELECTION.json`
- `04_PROTOCOLS/frozen_inputs/GOES16_FROZEN_SELECTION.json`
- `04_PROTOCOLS/frozen_inputs/GOES17_FROZEN_SELECTION.json`

The reusable implementation is `05_CODE/scripts/metric_aware_harmonization.py`. Its four unit tests in `05_CODE/tests/test_metric_aware_harmonization.py` cover exact closure, a synthetic component-improvement/downstream-deterioration case, conservative raw selection, and residual-interval abstention.

Deterministic build and validation entry points are:

- `05_CODE/scripts/build_si_evidence_tables.py`
- `05_CODE/scripts/build_covariance_regime_stress_test.py`
- `05_CODE/scripts/build_downstream_metric_framework_figure.py`
- `05_CODE/scripts/build_submission_figures.py`
- `05_CODE/scripts/build_supplementary_data_zip.py`
- `05_CODE/scripts/validate_reviewer_package.py`
- `scripts/run_all.sh`

The SI-table validation report is `02_EVIDENCE/si_tables/validation_report.json`. It records 94 unique candidates, 57 fixed intervals, eight design-stage attrition rows, 108 stage-event count rows, 20 model-selection rows, and 11 uncertainty-scope rows. Eight frozen city/interval payload hashes matched their manifests, and repeated builds were byte-identical. The 36-file source-hash manifest is `02_EVIDENCE/si_tables/source_provenance_manifest.csv`; repository-wide checksums are in `SHA256SUMS.txt`. Reviewer-facing evidence and validation inventories are also retained in `07_SUBMISSION/REMOTE_SENSING_CONSISTENCY_AND_DATA_AUDIT.md` and `07_SUBMISSION/Remote_Sensing_supplementary_data.zip`.
