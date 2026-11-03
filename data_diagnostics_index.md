# Data and diagnostics index

This index maps the manuscript and five SI tables to their computational evidence. Paths are relative to the versioned repository root. The source files preserve exact platform/time/support identifiers; legacy field names are not statements that the 2026 evaluation was prospective.

| Study item | File | Contents and reproduction role |
| --- | --- | --- |
| Main Table 1; Methods 2.1 | [fixed_interval_chronology.csv](evidence/si_tables/fixed_interval_chronology.csv) | Exact calendar windows, platform roles and design identifiers |
| Main Table 1; Methods 2.1 | [fixed_city_candidate_metadata.csv](evidence/si_tables/fixed_city_candidate_metadata.csv) | Candidate city/support metadata |
| Methods 2.1; cohort provenance | [index.csv](evidence/cohort_provenance/index.csv) | Upstream source hashes and roles; parent inventory, grouping and pilot exclusions |
| Methods 2.1; cohort provenance | [panel_city_base_corrected.csv](evidence/cohort_provenance/parent_city_base/panel_city_base_corrected.csv) | 5541-city parent inventory; mean support and grouping labels |
| Methods 2.1; cohort provenance | [prepare_goes_sunset_confirmation.py](evidence/cohort_provenance/select_confirmation/prepare_goes_sunset_confirmation.py) | Higher-support complete-covariate/pilot exclusion rules |
| Methods 2.1; cohort provenance | [prepare_goes19_2025_low_green_validation.py](evidence/cohort_provenance/select_lower/prepare_goes19_2025_low_green_validation.py) | Lower-support/geographic candidate rules |
| Methods 2.3; Figure 2 | [model_selection_summary.csv](evidence/si_tables/model_selection_summary.csv) | Complete candidate scores and one-standard-error selection |
| Methods 2.3; historical offsets | [external_hour_offsets_2019_2020.csv](evidence/si_tables/external_hour_offsets_2019_2020.csv) | Fitted core/ring hour offsets and calibration support |
| Methods 2.3; fitted models | [frozen_harmonization_model.joblib](evidence/analysis_outputs/multiplatform_harmonization/frozen_harmonization_model.joblib) | Initial serialized harmonization model; calibration data only |
| Methods 2.3; fitted models | [frozen_metric_aware_model.joblib](evidence/analysis_outputs/goes18_goes19_metric_harmonization/frozen_metric_aware_model.joblib) | 2025-calibrated final selector and fitted component models |
| Results 3.1; Figure 3 | [cross_sample_rmse_with_external.csv](evidence/tables/cross_sample_rmse_with_external.csv) | All five cohort RMSE comparisons |
| Results 3.2; SI S1 | [exact_mse_budgets_with_external.csv](evidence/tables/exact_mse_budgets_with_external.csv) | Hourly and transition MSE components and exact identity closure |
| Methods 2.6; Figures 3–5 | [mse_budget_2026_crossed_bootstrap.parquet](evidence/bootstrap/mse_budget_2026_crossed_bootstrap.parquet) | 5000 crossed city–interval resamples of fixed final models |
| Methods 2.6; Figure 5 | [validation_2021_bootstrap_summary.csv](evidence/external_replication/validation_2021_bootstrap_summary.csv) | Historical 2021 uncertainty summaries |
| Methods 2.6; Results 3.4; SI S5 | [REVIEWER_DIAGNOSTICS.md](REVIEWER_DIAGNOSTICS.md) | Direct index to every physical diagnostic dimension and supporting source |
| Methods 2.7; Results 3.5; SI S2 | [component_and_contrast_metrics.csv](evidence/quality/component_and_contrast_metrics.csv) | Recommended/strict-quality metrics, including restricted three-city comparisons |
| Methods 2.7; Results 3.5; SI S2 | [native_cloud_sensitivity.csv](evidence/native/native_cloud_sensitivity.csv) | Eight selected-date cloud-mask/buffer comparisons; scan support |
| Methods 2.7; SI S4 | [full_metrics.csv](evidence/surface/full_metrics.csv) | Historical raw-product station metrics |
| Methods 2.7; SI S4 | [compact_station_metrics.csv](evidence/surface/modern/compact_station_metrics.csv) | 2025/2026 raw GOES-18/19 station benchmark metrics |
| Methods 2.7; SI S4 | [native_source_manifest.csv](evidence/surface/modern/native_source_manifest.csv) | Exact modern satellite source-object names and support |
| Methods 2.7; SI S4 | [ground_source_manifest.csv](evidence/surface/modern/ground_source_manifest.csv) | Ground data provenance and source files |
| Ground sensitivity; emissivity scope | [modern_ground_sensitivity.csv](evidence/surface/modern/modern_ground_sensitivity.csv) | Ground radiometry/emissivity scenarios; no ABI retrieval-input perturbation |
| SI S1–S5 | [table_s1_publication.csv](evidence/si_tables/table_s1_publication.csv) | Compact publication S1; S2–S5 are in the same directory |
| Offline scientific reproduction | [reproduce.py](scripts/reproduce.py) | Portable processed-data fitting/evaluation and bootstrap pipeline |
| Modern station reproduction | [reproduce_modern_surface.py](scripts/reproduce_modern_surface.py) | Modern benchmark recomputation; random seed20261029 is explicit here |
| Model/software configuration | [requirements.txt](requirements.txt) | Pinned direct dependencies |
| Model/software configuration | [requirements-lock.txt](requirements-lock.txt) | Full tested offline environment |
| Model/software configuration | [environment.yml](environment.yml) | Conda-style Python and dependency specification |
| Source manifests; reproducibility | [input_manifest.json](evidence/reproducibility/input_manifest.json) | Input identities and scientific reproduction evidence |

The corresponding CSV records file hashes and sizes. Read the main README for reproduction commands and boundaries. SI S1–S5 contain compact summaries; the indexed data retain the detailed evidence. Models are calibrated on 2025 or earlier data as appropriate; 2026 outcomes are not used for fitting or selection.
