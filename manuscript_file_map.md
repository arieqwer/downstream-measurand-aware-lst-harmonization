# Manuscript to computational file map

This map describes the manuscript and five-table SI for version v2.1.2-r1. Complete paths, descriptions and evidence roles are in [data_diagnostics_index.md](data_diagnostics_index.md).

| Paper item | Supporting files |
| --- | --- |
| Methods 2.1; main Table 1; cohort provenance | [Fixed interval chronology](evidence/si_tables/fixed_interval_chronology.csv), [candidate metadata](evidence/si_tables/fixed_city_candidate_metadata.csv), [upstream provenance index](evidence/cohort_provenance/index.csv) |
| Methods 2.3–2.4; Figure 2; model selection | [Model-selection scores](evidence/si_tables/model_selection_summary.csv), [historical offsets](evidence/si_tables/external_hour_offsets_2019_2020.csv), fitted models under `evidence/analysis_outputs/` |
| Figures 3–5; MSE accounting and uncertainty | [Cohort RMSE results](evidence/tables/cross_sample_rmse_with_external.csv), [exact MSE budgets](evidence/tables/exact_mse_budgets_with_external.csv), `evidence/bootstrap/`, `evidence/external_replication/` |
| Methods 2.7; Results 3.5; quality and cloud screening | [Quality metrics](evidence/quality/component_and_contrast_metrics.csv), [sampled cloud sensitivity](evidence/native/native_cloud_sensitivity.csv) |
| Independent raw-product station comparisons | [Historical metrics](evidence/surface/full_metrics.csv), [modern metrics](evidence/surface/modern/compact_station_metrics.csv), [modern source manifest](evidence/surface/modern/native_source_manifest.csv) |
| SI Tables S1–S5 | [S1](evidence/si_tables/table_s1_publication.csv), [S2](evidence/si_tables/table_s2_publication.csv), [S3](evidence/si_tables/table_s3_publication.csv), [S4](evidence/si_tables/table_s4_publication.csv), [S5](evidence/si_tables/table_s5_publication.csv) |
| All six figure files and portable regeneration | `outputs/figures/`; [figure reproduction entry point](scripts/reproduce_figures.py) |
| Physical diagnostic dimensions and limitations | [Reviewer diagnostics index](REVIEWER_DIAGNOSTICS.md) |

The assessment concerns inter-platform consistency at the scientific measurand. The 2026 analysis is a post hoc temporal evaluation at the same 75 cities used for 2025 calibration. The three-station benchmark evaluates raw station products and does not independently validate the complete urban core–ring workflow. Statistical covariance diagnostics and limited sensitivity comparisons do not uniquely identify physical causes.
