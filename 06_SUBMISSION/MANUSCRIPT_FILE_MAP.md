# Manuscript to computational file map

This map describes the clean manuscript and five-table SI included in test prerelease v2.1.2-r0. Complete paths, descriptions and evidence roles are in [DATA_DIAGNOSTICS_INDEX.md](../DATA_DIAGNOSTICS_INDEX.md).

| Paper item | Supporting files |
| --- | --- |
| Methods 2.1; main Table 1; cohort provenance | [Fixed interval chronology](../02_EVIDENCE/si_tables/fixed_interval_chronology.csv), [candidate metadata](../02_EVIDENCE/si_tables/fixed_city_candidate_metadata.csv), [upstream provenance index](../02_EVIDENCE/cohort_provenance/index.csv) |
| Methods 2.3–2.4; Figure 2; model selection | [Model-selection scores](../02_EVIDENCE/si_tables/model_selection_summary.csv), [historical offsets](../02_EVIDENCE/si_tables/external_hour_offsets_2019_2020.csv), fitted models under `02_EVIDENCE/analysis_outputs/` |
| Figures 3–5; MSE accounting and uncertainty | [Cohort RMSE results](../02_EVIDENCE/tables/cross_sample_rmse_with_external.csv), [exact MSE budgets](../02_EVIDENCE/tables/exact_mse_budgets_with_external.csv), `02_EVIDENCE/bootstrap/`, `02_EVIDENCE/external_replication/` |
| Methods 2.7; Results 3.5; quality and cloud screening | [Quality metrics](../02_EVIDENCE/quality/component_and_contrast_metrics.csv), [sampled cloud sensitivity](../02_EVIDENCE/native/native_cloud_sensitivity.csv) |
| Independent raw-product station comparisons | [Historical metrics](../02_EVIDENCE/surface/full_metrics.csv), [modern metrics](../02_EVIDENCE/surface/modern/compact_station_metrics.csv), [modern source manifest](../02_EVIDENCE/surface/modern/native_source_manifest.csv) |
| SI Tables S1–S5 | [S1](../02_EVIDENCE/si_tables/Table_S1_publication.csv), [S2](../02_EVIDENCE/si_tables/Table_S2_publication.csv), [S3](../02_EVIDENCE/si_tables/Table_S3_publication.csv), [S4](../02_EVIDENCE/si_tables/Table_S4_publication.csv), [S5](../02_EVIDENCE/si_tables/Table_S5_publication.csv) |
| All six figure files and portable regeneration | `outputs/figures/`; [figure reproduction entry point](../scripts/reproduce_figures.py) |
| Physical diagnostic dimensions and limitations | [Reviewer diagnostics index](../REVIEWER_DIAGNOSTICS.md) |

The assessment concerns inter-platform consistency at the scientific measurand. The 2026 analysis is a post hoc temporal evaluation at the same 75 cities used for 2025 calibration. The three-station benchmark evaluates raw station products and does not independently validate the complete urban core–ring workflow. Statistical covariance diagnostics and limited sensitivity comparisons do not uniquely identify physical causes.
