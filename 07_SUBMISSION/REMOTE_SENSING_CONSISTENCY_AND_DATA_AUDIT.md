# Remote Sensing manuscript, Supplementary Materials, and data audit

**Audit date:** 28 August 2026  
**Scope:** main manuscript, Supplementary Materials, Figures 1–4 and their captions, Supplementary Data S1–S15, the reviewer-facing ZIP archive, frozen protocols/manifests, and the private reviewer repository.

## Outcome

- The revised main manuscript and Supplementary Materials preserve all analyzed samples, models, thresholds, dates, numerical results, and scientific conclusions.
- The abstract is one paragraph and 252 words under the submission-package counter. Highlights, Introduction, Methods, Discussion, Conclusions, quality terminology, and study-specific novelty language were revised as requested where supported.
- Figure order is Figure 1, Figure 2 (cross-cohort synthesis), Figure 3 (deterministic covariance-regime stress test), and Figure 4, in strict order of first citation. All main-text, SI, and caption-file cross-references match.
- Figure 1 panel a now shows the complete workflow with wider horizontal spacing, sentence-case box text, a lower measurand-action row, and no arrow/label overlap. Panel b has no vertical year gridlines.
- Main Table 1 and SI Tables S1–S5, S7, and S9 use at least 8 pt text. All other table text is also at least 8 pt.
- The main article contains nine displayed equations and the Supplementary Materials contain nine displayed equations. All 18 are native editable Microsoft Word equation objects.
- Neither Word file contains author-applied line numbering.
- The rendered 17-page manuscript and 19-page supplement were inspected page by page. No clipped text, split figure caption, missing panel, overlapping object, or unreadable table was found.
- Reported values, sample sizes, intervals, platform pairings, measurement terms, figure/table numbers, Supplementary Data identifiers, citations, and section cross-references were checked across the manuscript, SI, figure-caption assets, and retained evidence. No unresolved numerical or cross-reference mismatch remains.

## Editorial decisions

- The DQF wording was changed to “good- and medium-quality LST retrievals (DQF 0–1),” with DQF 0 defined as good quality and DQF 1 as medium quality, without changing the analyzed sample.
- Zhang et al. (2025; DOI 10.3389/frsen.2025.1670390) was added only as prior covariance-aware derived-product work; the manuscript does not claim covariance itself as new.
- “Exact MSE decomposition,” “evaluation design,” “validation design,” “residual-interval rule,” “directionally resolved,” and “abstained” are used consistently in article-facing text. Legacy machine fields containing `gate` or `certified` remain unchanged for schema/provenance compatibility and are explicitly mapped in Table S12.
- The standalone reproducibility subsection was removed from the main text; its essential software statement remains at the end of Section 2.8, while detailed tests and machine checks remain in SI S9.
- The factual generative-AI disclosure was retained in Materials and Methods and Acknowledgments because the documented assistance extended beyond text-only editing to software implementation, validation checks, and figure-generation scripts.
- US English was standardized outside official titles, literal field names, code identifiers, and frozen protocol text.

## Calendar and hydroclimate provenance

- **2022–2024:** the 31 intervals came from a pre-existing, outcome-independent warm-season hydroclimatic event census. Every eligible recurring June–August eight-day interval satisfying the archived heat-count and severity-dispersion criteria was retained. Evaluated GOES discrepancies and harmonization results did not select the dates.
- **2025:** the ten intervals came from the corresponding pre-existing ERA5-Land-only heat/severity census; all eligible intervals were retained. Evaluated GOES-18/19 discrepancies and harmonization results did not select the dates.
- **2026:** eight consecutive eight-day windows beginning 1 June were generated and frozen before extraction of either 2026 platform; they were not selected through a hydroclimatic event screen.
- **2019–2021:** the dates were calendar-fixed and frozen before GOES-17 file listing or extraction. The archived records do not document a hydroclimatic selection rule or a more specific scientific rationale for the particular dates. No rationale was invented.
- The implemented true-night exposure uses ERA5-Land hourly `temperature_2m` over the urban core for local-solar hours 22:00–<06:00, averaged by eight-day step and ranked with average ties within city across recurring steps. Hydroclimatic severity is the mean of 100 minus the root-zone soil-moisture percentile and the vapor-pressure-deficit percentile, with percentiles constructed within city and recurring step over 2003–2025. SI S1 documents the executable implementation.
- **Provenance note:** shorthand in an archived frozen protocol can be read as applying the true-night percentile within city and recurring step, whereas the executable field-generation code ranks true-night temperature within city across recurring steps. The SI follows the executable implementation that generated the processed field. No result or frozen protocol was altered; this discrepancy is documented rather than silently harmonized.

## Supplementary Data S1–S15

| Data | Package-relative file | Verified dimensions | Status |
|---|---|---:|---|
| S1 | `02_EVIDENCE/si_tables/fixed_city_candidate_metadata.csv` | 94 × 37 | Pass |
| S2 | `02_EVIDENCE/si_tables/fixed_interval_chronology.csv` | 57 × 12 | Pass |
| S3 | `02_EVIDENCE/si_tables/cohort_event_analysis_counts.csv` | 108 × 13 | Pass |
| S4 | `02_EVIDENCE/si_tables/model_selection_summary.csv` | 20 × 12 | Pass |
| S5 | `02_EVIDENCE/si_tables/external_hour_offsets_2019_2020.csv` | 10 × 6 | Pass |
| S6 | `02_EVIDENCE/si_tables/uncertainty_gate_2026_by_cohort_event.csv` | 11 × 21 | Pass |
| S7 | `02_EVIDENCE/si_tables/source_provenance_manifest.csv` | 36 × 6 | Pass |
| S8 | `02_EVIDENCE/si_tables/validation_report.json` | JSON; status `pass` | Pass |
| S9 | `02_EVIDENCE/tables/cross_sample_rmse_with_external.csv` | 15 × 5 | Pass |
| S10 | `02_EVIDENCE/tables/exact_mse_budgets_with_external.csv` | 10 × 41 | Pass |
| S11 | `02_EVIDENCE/tables/mse_budget_2026_bootstrap_summary.csv` | 12 × 7 | Pass |
| S12 | `02_EVIDENCE/external_replication/validation_2021_bootstrap_summary.csv` | 16 × 7 | Pass |
| S13 | `02_EVIDENCE/external_replication/validation_2021_event_influence.csv` | 8 × 41 | Pass |
| S14 | `02_EVIDENCE/bootstrap/mse_budget_2026_crossed_bootstrap.parquet` | 10,000 × 26 | Pass |
| S15 | `02_EVIDENCE/bootstrap/validation_2021_crossed_bootstrap.parquet` | 10,000 × 39 | Pass |

All 15 numbered files exist at the Table S12 paths, have the stated dimensions, parse successfully, are present in `Remote_Sensing_supplementary_data.zip`, and are byte-identical to their project copies. The deterministic ZIP contains 25 expected members and passes CRC testing.

## Machine validation

- The private reviewer repository rebuilt successfully with `scripts/run_all.sh`.
- The independent reviewer validator passed 19 of 19 checks: 15 five-cohort RMSE rows, ten exact MSE budgets, 30 observed identity checks, 2026 residual-interval counts, both 10,000-row bootstrap files, 60,000 bootstrap identity checks, and all 36 source-provenance hashes.
- Four reusable-module unit tests passed.
- The deterministic stress test reproduced 9,216 correlation cells and 11,612,160 configurations; the maximum direct-versus-reconstructed discrepancy was 8.88 × 10⁻¹⁶ normalized MSE units.
- Word OOXML packages passed CRC/XML checks; every table run has an explicit size of at least 16 half-points (8 pt); current Figure 1–4 PNGs are embedded byte-for-byte; all 26 references are cited and numbered contiguously.

No missing or mismatched submission-data artifact remains. The only documentation limits are the unrecorded specific rationale for the fixed 2019–2021 dates and the archived-protocol shorthand discrepancy noted above.
