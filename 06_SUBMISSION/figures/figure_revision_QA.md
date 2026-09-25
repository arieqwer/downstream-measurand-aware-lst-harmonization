# Figure revision QA

## Scope and status

- Status: `all_frozen_source_checks_passed`.
- This run changed visualization code and generated figure/audit files only. It did not edit the manuscript or Supplementary Materials DOCX.
- No scientific analysis, refitting, resampling, or change to values, dates, cohorts, membership, terminology, or uncertainty estimates was performed.
- Figure 3c was deleted. No directional-support count, abstention count, or sign-agreement text remains in revised Figure 3.

## Exact panel sources

| Panel | Authoritative plotted/checking source |
| --- | --- |
| Figure 1a | No numerical input; existing workflow wording and hierarchy only |
| Figure 1b | 02_EVIDENCE/si_tables/fixed_city_candidate_metadata.csv (study symbols); data/natural_earth/physical/ne_110m_land.shp, data/natural_earth/cultural/ne_110m_admin_0_boundary_lines_land.shp, and data/natural_earth/cultural/ne_50m_admin_1_states_provinces_lines.shp (cartographic context; no separate coastline layer) |
| Figure 1c | 02_EVIDENCE/si_tables/fixed_interval_chronology.csv (plot positions); 02_EVIDENCE/si_tables/cohort_event_analysis_counts.csv (shared-date and support-count cross-checks) |
| Figure 2a–d | 02_EVIDENCE/si_tables/model_selection_summary.csv |
| Figure 3a | 02_EVIDENCE/tables/downstream_metric_framework_figure_rmse_source.csv |
| Figure 3b | 02_EVIDENCE/tables/downstream_metric_framework_figure_budget_source.csv |

Supplementary Data mappings used here are: S1 = `02_EVIDENCE/si_tables/fixed_city_candidate_metadata.csv`; S2 = `02_EVIDENCE/si_tables/fixed_interval_chronology.csv`; S3 = `02_EVIDENCE/si_tables/cohort_event_analysis_counts.csv`; and S4 = `02_EVIDENCE/si_tables/model_selection_summary.csv`.

## Figure 1b city-symbol and support audit

- Data S1 contains 94 unique fixed western candidates: 51 original and 43 expansion candidates.
- The 2025 calibration and 2026 holdout membership flags are identical and retain 75 cities: 44 original + 31 expansion = 75.
- The 2021 external analyzed support is an exact 69-city subset of those 75; six retained 2025–2026 cities were not retained in 2021.
- Rendered map marks: 94 base city symbols plus six thin black outer-ring overlays. The overlays do not represent additional cities.
- Candidate-only symbols: 19; retained original symbols: 44; retained expansion symbols: 31; 2021-exclusion rings: 6.
- Longitude and latitude were plotted directly from Data S1 in Plate Carree coordinates; no coordinate transformation, displacement, or jitter was applied.
- The rectangular map extent is exactly -125° to -100° longitude and 31° to 51° latitude. The right frame remains exactly 100°W; the separate in-figure cutoff annotation was removed at the author's request.
- The separate coastline layer, all graticule-line layers, and the former dashed cutoff line were removed. The land/water fills, medium-gray country boundaries, and thin light-gray state/province boundaries remain.
- The compact 94 → 75 → 69 support-flow graphic is outside the map and preserves the 19 candidate-only and six 2021-exclusion annotations.
- Symbol size does not encode observation count, and symbol shape does not encode platform pairing.

## Figure 1c interval audit

- `Figure1c_interval_audit.csv` is a direct eight-column extraction of all 57 Data S2 source rows.
- All 57 source rows have `interval_days_inclusive = 8`, and recomputing `(end_date − start_date) + 1` gives eight days for every row.
- Source counts: four 2019–2020 G17/16 calibration intervals; four 2021 G17/16 validation intervals; 31 G18/16 intervals in 2022–2024; ten G18/19 intervals in 2025; and eight prespecified G18/19 intervals in 2026.
- The 31 G18/16 dates are plotted on both the original-derivation and expansion-evaluation tracks. The ten 2025 dates are plotted on both the original- and expansion-evaluation tracks. These equivalences were checked against Data S3.
- Therefore the chronology uses 57 authoritative interval rows/unique windows and renders 98 track-specific ticks: 4 + 4 + 31 + 31 + 10 + 10 + 8.
- Every tick x-position comes directly from the corresponding `start_date`. No dates were aggregated or merged into min–max seasonal blocks.

### All 57 source rows and plotting basis

| design_id | reference_platform | source_platform | analysis_role | event_time_id | start_date | end_date | interval_days_inclusive | Plot-position basis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| goes17_goes16_2019_2021 | GOES17 | GOES16 | calibration | 3001 | 2019-06-01 | 2019-06-08 | 8 | Directly from start_date (2019-06-01) |
| goes17_goes16_2019_2021 | GOES17 | GOES16 | calibration | 3002 | 2019-07-17 | 2019-07-24 | 8 | Directly from start_date (2019-07-17) |
| goes17_goes16_2019_2021 | GOES17 | GOES16 | calibration | 3003 | 2020-06-01 | 2020-06-08 | 8 | Directly from start_date (2020-06-01) |
| goes17_goes16_2019_2021 | GOES17 | GOES16 | calibration | 3004 | 2020-07-17 | 2020-07-24 | 8 | Directly from start_date (2020-07-17) |
| goes17_goes16_2019_2021 | GOES17 | GOES16 | validation | 3005 | 2021-06-01 | 2021-06-08 | 8 | Directly from start_date (2021-06-01) |
| goes17_goes16_2019_2021 | GOES17 | GOES16 | validation | 3006 | 2021-06-17 | 2021-06-24 | 8 | Directly from start_date (2021-06-17) |
| goes17_goes16_2019_2021 | GOES17 | GOES16 | validation | 3007 | 2021-07-03 | 2021-07-10 | 8 | Directly from start_date (2021-07-03) |
| goes17_goes16_2019_2021 | GOES17 | GOES16 | validation | 3008 | 2021-07-19 | 2021-07-26 | 8 | Directly from start_date (2021-07-19) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 894 | 2022-06-10 | 2022-06-17 | 8 | Directly from start_date (2022-06-10) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 895 | 2022-06-18 | 2022-06-25 | 8 | Directly from start_date (2022-06-18) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 896 | 2022-06-26 | 2022-07-03 | 8 | Directly from start_date (2022-06-26) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 897 | 2022-07-04 | 2022-07-11 | 8 | Directly from start_date (2022-07-04) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 898 | 2022-07-12 | 2022-07-19 | 8 | Directly from start_date (2022-07-12) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 899 | 2022-07-20 | 2022-07-27 | 8 | Directly from start_date (2022-07-20) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 900 | 2022-07-28 | 2022-08-04 | 8 | Directly from start_date (2022-07-28) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 901 | 2022-08-05 | 2022-08-12 | 8 | Directly from start_date (2022-08-05) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 902 | 2022-08-13 | 2022-08-20 | 8 | Directly from start_date (2022-08-13) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 903 | 2022-08-21 | 2022-08-28 | 8 | Directly from start_date (2022-08-21) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 904 | 2022-08-29 | 2022-09-05 | 8 | Directly from start_date (2022-08-29) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 941 | 2023-06-18 | 2023-06-25 | 8 | Directly from start_date (2023-06-18) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 942 | 2023-06-26 | 2023-07-03 | 8 | Directly from start_date (2023-06-26) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 943 | 2023-07-04 | 2023-07-11 | 8 | Directly from start_date (2023-07-04) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 944 | 2023-07-12 | 2023-07-19 | 8 | Directly from start_date (2023-07-12) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 945 | 2023-07-20 | 2023-07-27 | 8 | Directly from start_date (2023-07-20) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 946 | 2023-07-28 | 2023-08-04 | 8 | Directly from start_date (2023-07-28) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 947 | 2023-08-05 | 2023-08-12 | 8 | Directly from start_date (2023-08-05) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 948 | 2023-08-13 | 2023-08-20 | 8 | Directly from start_date (2023-08-13) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 949 | 2023-08-21 | 2023-08-28 | 8 | Directly from start_date (2023-08-21) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 950 | 2023-08-29 | 2023-09-05 | 8 | Directly from start_date (2023-08-29) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 987 | 2024-06-17 | 2024-06-24 | 8 | Directly from start_date (2024-06-17) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 988 | 2024-06-25 | 2024-07-02 | 8 | Directly from start_date (2024-06-25) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 989 | 2024-07-03 | 2024-07-10 | 8 | Directly from start_date (2024-07-03) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 990 | 2024-07-11 | 2024-07-18 | 8 | Directly from start_date (2024-07-11) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 991 | 2024-07-19 | 2024-07-26 | 8 | Directly from start_date (2024-07-19) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 992 | 2024-07-27 | 2024-08-03 | 8 | Directly from start_date (2024-07-27) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 993 | 2024-08-04 | 2024-08-11 | 8 | Directly from start_date (2024-08-04) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 994 | 2024-08-12 | 2024-08-19 | 8 | Directly from start_date (2024-08-12) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 995 | 2024-08-20 | 2024-08-27 | 8 | Directly from start_date (2024-08-20) |
| goes18_goes16_2022_2024 | GOES18 | GOES16 | model_derivation_original_and_spatial_evaluation_expansion | 996 | 2024-08-28 | 2024-09-04 | 8 | Directly from start_date (2024-08-28) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1033 | 2025-06-18 | 2025-06-25 | 8 | Directly from start_date (2025-06-18) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1034 | 2025-06-26 | 2025-07-03 | 8 | Directly from start_date (2025-06-26) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1035 | 2025-07-04 | 2025-07-11 | 8 | Directly from start_date (2025-07-04) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1036 | 2025-07-12 | 2025-07-19 | 8 | Directly from start_date (2025-07-12) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1037 | 2025-07-20 | 2025-07-27 | 8 | Directly from start_date (2025-07-20) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1038 | 2025-07-28 | 2025-08-04 | 8 | Directly from start_date (2025-07-28) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1039 | 2025-08-05 | 2025-08-12 | 8 | Directly from start_date (2025-08-05) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1040 | 2025-08-13 | 2025-08-20 | 8 | Directly from start_date (2025-08-13) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1041 | 2025-08-21 | 2025-08-28 | 8 | Directly from start_date (2025-08-21) |
| goes18_goes19_2025 | GOES18 | GOES19 | initial_model_evaluation_and_metric_aware_calibration | 1042 | 2025-08-29 | 2025-09-05 | 8 | Directly from start_date (2025-08-29) |
| goes18_goes19_2026 | GOES18 | GOES19 | prospective_temporal_holdout | 2001 | 2026-06-01 | 2026-06-08 | 8 | Directly from start_date (2026-06-01) |
| goes18_goes19_2026 | GOES18 | GOES19 | prospective_temporal_holdout | 2002 | 2026-06-09 | 2026-06-16 | 8 | Directly from start_date (2026-06-09) |
| goes18_goes19_2026 | GOES18 | GOES19 | prospective_temporal_holdout | 2003 | 2026-06-17 | 2026-06-24 | 8 | Directly from start_date (2026-06-17) |
| goes18_goes19_2026 | GOES18 | GOES19 | prospective_temporal_holdout | 2004 | 2026-06-25 | 2026-07-02 | 8 | Directly from start_date (2026-06-25) |
| goes18_goes19_2026 | GOES18 | GOES19 | prospective_temporal_holdout | 2005 | 2026-07-03 | 2026-07-10 | 8 | Directly from start_date (2026-07-03) |
| goes18_goes19_2026 | GOES18 | GOES19 | prospective_temporal_holdout | 2006 | 2026-07-11 | 2026-07-18 | 8 | Directly from start_date (2026-07-11) |
| goes18_goes19_2026 | GOES18 | GOES19 | prospective_temporal_holdout | 2007 | 2026-07-19 | 2026-07-26 | 8 | Directly from start_date (2026-07-19) |
| goes18_goes19_2026 | GOES18 | GOES19 | prospective_temporal_holdout | 2008 | 2026-07-27 | 2026-08-03 | 8 | Directly from start_date (2026-07-27) |

## Figure 2 model-selection audit

- Only the 16 rows with `selection_stage = metric_aware_calibration_2025` were plotted; no 2022–2024 hour-spline result was included.
- Means, one-standard-error intervals, cutoffs, selected models, and minimum models were checked numerically against Supplementary Data S4 before rendering.
- The Supplementary Data S4 byte hash remains `1de247585987d64021fd95e3189ca36a7800b3c5dd9b09868c4617ff7bb9bdf1`; all values are byte- and numerically identical to the previously verified model-selection source.
- All ordinary means use the same neutral dark-gray point encoding. The compact legend now shows mean ± 1 SE, selection by an orange star, and the minimum by a black ring.

| Panel | Candidate | Mean | SE | Cutoff | Selected | Minimum |
| --- | --- | --- | --- | --- | --- | --- |
| Hourly core LST | Raw | 1.0000000000 | 0.0000000000 | 0.4965437059 | No | No |
| Hourly core LST | Hour offset | 0.5246671691 | 0.0573069129 | 0.4965437059 | No | No |
| Hourly core LST | Geometry ridge | 0.4492364378 | 0.0473072681 | 0.4965437059 | Yes | Yes |
| Hourly core LST | Scene GBDT | 0.4784316931 | 0.0445792379 | 0.4965437059 | No | No |
| Hourly ring LST | Raw | 1.0000000000 | 0.0000000000 | 0.5031859688 | No | No |
| Hourly ring LST | Hour offset | 0.4631897722 | 0.0399961966 | 0.5031859688 | Yes | Yes |
| Hourly ring LST | Geometry ridge | 0.5735954008 | 0.0855788041 | 0.5031859688 | No | No |
| Hourly ring LST | Scene GBDT | 0.4933674018 | 0.0410295724 | 0.5031859688 | No | No |
| Hourly core–ring contrast | Raw | 1.0000000000 | 0.0000000000 | 1.0301746537 | Yes | No |
| Hourly core–ring contrast | Hour offset | 1.0076674000 | 0.0118508768 | 1.0301746537 | No | No |
| Hourly core–ring contrast | Geometry ridge | 0.9928781247 | 0.0372965290 | 1.0301746537 | No | Yes |
| Hourly core–ring contrast | Scene GBDT | 1.0558492579 | 0.0479140021 | 1.0301746537 | No | No |
| Core–ring transition | Raw | 1.0000000000 | 0.0000000000 | 1.0000000000 | Yes | Yes |
| Core–ring transition | Mean offset | 1.0158864648 | 0.0056637602 | 1.0000000000 | No | No |
| Core–ring transition | Transition ridge | 1.7844681850 | 0.3175400495 | 1.0000000000 | No | No |
| Core–ring transition | Transition GBDT | 1.1288670820 | 0.0503290001 | 1.0000000000 | No | No |

## Figure 3 data-preservation audit

- Revised Figure 3 contains two aligned panels only: 15 frozen RMSE-reduction points in panel a and five frozen hourly MSE-decomposition rows in panel b.
- Panel a uses all five evaluation cohorts and the same core, ring, and core–ring-contrast values/order as the frozen plotting source.
- Panel b uses the unchanged component-variance, differential-bias, covariance-loss, and net-downstream-gain columns. The covariance-loss penalty remains plotted as a negative contribution, and source decomposition closure remains below `1×10−10 K²`.
- Figure 3 source hashes remain unchanged (`rmse`: `3de82ac0bd5fb2ad7e5f0d7901d2e5956980f6f86d154a30e93eec85878ce8af`; `mse`: `368556f1923ae22dfdd5e2c94574257968aaf271b0860c7522b98e94a0ed92a9`), so every retained Figure 3 value is identical to the previously verified version.
- The panel-b legend begins at the left edge of the panel-b plotting region and extends rightward without changing its wording; the complete `Covariance-loss penalty` label is contained within the export.
- Former directional-support panel c was removed completely; its source is not loaded by the revised Figure 3 builder.

## Figure caption and numbering record

- The current figure sequence is Figure 1 workflow/domain/chronology; Figure 2 one-standard-error selection; Figure 3 cross-cohort performance/decomposition; Figure 4 covariance-regime stress test; and Figure 5 replication/holdout diagnostics.
- Figure 1c uses thin ticks for the exact start dates of fixed inclusive eight-day windows; shared dates appear on both relevant cohort tracks.
- Figure 2 uses gray mean ± one-SE marks, orange one-SE cutoff lines, light-gray raw = 1.0 reference lines, stars for selected models, and rings for minimum-mean models. Panel-specific x-axis ranges differ.
- Figure 3 contains only cross-cohort RMSE changes and exact hourly MSE decomposition. Its former directional-support panel is not included. Directional-support diagnostics are in Figure 5.
- This repository update did not edit the manuscript or Supplementary Materials DOCX.

## Render and export audit

| Figure | PNG dimensions | Requested export | Stored PNG metadata | PNG file |
| --- | --- | --- | --- | --- |
| Figure 1 | 4475 × 6240 px | 600 dpi | 599.9988 × 599.9988 dpi | Figure_1_workflow_domain_chronology.png |
| Figure 2 | 3688 × 2837 px | 600 dpi | 599.9988 × 599.9988 dpi | Figure_2_one_se_model_selection.png |
| Figure 3 | 4611 × 1731 px | 600 dpi | 599.9988 × 599.9988 dpi | Figure_3_component_downstream_results.png |

PNG files were written with Matplotlib `dpi=600`. PNG stores resolution as an integer pixels-per-metre value, which Pillow reports as approximately 599.9988 dpi; this is the standard metadata representation of nominal 600 dpi. The export used tight artist bounds plus a nonzero 0.05-inch safety pad.

## Final clipping inspection

- Final PNGs were inspected at the full left and right extents after export.
- Figure 1 contains the complete workflow labels, external geographic ticks, map legend, support-flow text, and chronology without clipping; no separate `100°W analysis cutoff` label remains.
- Figure 2 contains the complete three-item legend, all four separated panel letters and titles, cutoff labels, candidate labels, and annotations without clipping; the former global x-axis label was removed at the author's request.
- Figure 3 contains the complete `Covariance-loss penalty` legend text, panel-b y-axis label, all tick labels, panel letters `a` and `b`, and the full left/right extent of both panels without clipping.
- No text or marker touches or extends beyond the exported PNG canvas.

## Source hashes

- `cities`: `bc682ab609298bf36ba4841693cb26895525e7ec085c3c87a0fbc1b170707378` — `02_EVIDENCE/si_tables/fixed_city_candidate_metadata.csv`
- `chronology`: `ba96cdcc9a3f8ef9b00aa61bee3676977714ed590392ca79ad4be2d97c817b23` — `02_EVIDENCE/si_tables/fixed_interval_chronology.csv`
- `counts`: `34c101b4c79e6340bdc87eb8f26f75cef001ab277ef50c132cd12e39cee34be1` — `02_EVIDENCE/si_tables/cohort_event_analysis_counts.csv`
- `model_selection`: `1de247585987d64021fd95e3189ca36a7800b3c5dd9b09868c4617ff7bb9bdf1` — `02_EVIDENCE/si_tables/model_selection_summary.csv`
- `rmse`: `3de82ac0bd5fb2ad7e5f0d7901d2e5956980f6f86d154a30e93eec85878ce8af` — `02_EVIDENCE/tables/downstream_metric_framework_figure_rmse_source.csv`
- `mse`: `368556f1923ae22dfdd5e2c94574257968aaf271b0860c7522b98e94a0ed92a9` — `02_EVIDENCE/tables/downstream_metric_framework_figure_budget_source.csv`

### Cartographic reference-layer hashes

- `land`: `8689e6932b8e370e2ca4587cf3ba21e460b1235db37b6ed3c172c35b4a6088de` — `data/natural_earth/physical/ne_110m_land.shp`
- `countries`: `d19f784f92626816c064f878571f61bc43ec7bfc407666ce6a450d6e757afff0` — `data/natural_earth/cultural/ne_110m_admin_0_boundary_lines_land.shp`
- `states_provinces`: `c117e2f2d2776e2d0504f32be833bbbd9fb7b4683cf70e2298b5cc385a25b883` — `data/natural_earth/cultural/ne_50m_admin_1_states_provinces_lines.shp`

## Output hashes

- Figure 1 PNG: `7bb534d88d4483a4d1006a980adea1df03f2185eaccc748bf7681a62ca50be24`
- Figure 2 PNG: `20ec1dd2fd0840c5c6b95627d8b7545e1cd2f673debb15bcdcef70cbd5ab93c2`
- Figure 3 PNG: `b1bfb1dbfd217efa7c01812d8942a8b51dce86194191fa5abd8e33b6a969cff4`
