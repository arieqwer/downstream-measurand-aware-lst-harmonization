# Supplementary design and decision tables

This directory contains deterministic, source-traceable design and decision tables for the manuscript and SI. No frozen source file was modified.

## Contents

- `fixed_city_candidate_metadata.csv`: all 94 fixed candidates, city names and coordinates, original/expansion descriptors, 2026 GOES-18/19 grid support, candidate-pool flags, and analysis-membership flags (including reproducibly reconstructed external-calibration membership).
- `fixed_interval_chronology.csv`: the 31 historical, 10 calibration/evaluation, 8 prospective holdout, and 8 external calibration/validation intervals (57 rows total).
- `cohort_attrition_summary.csv`: candidate-to-analysis retention for all eight derivation, evaluation, calibration, holdout, and external stages.
- `cohort_event_analysis_counts.csv`: event-level analyzed-city, hourly-row, and eligible-transition counts. External calibration transitions are blank because transition calibration was not part of that design.
- `model_selection_summary.csv`: every initial and metric-aware candidate model, exact parsimony rank, cross-validation score, one-standard-error threshold, and frozen selection.
- `external_hour_offsets_2019_2020.csv`: byte-identical copy of the ten frozen GOES-17 minus GOES-16 calibration offsets.
- `uncertainty_gate_2026_by_cohort_event.csv`: the three cohort-level and eight event-level uncertainty results, including integer numerators and the prespecified 85–95% coverage-band/90%-reference-sign-agreement criteria. Only the pooled combined row is the formal frozen decision scope; subgroup and event rows diagnose transport.
- `source_provenance_manifest.csv`: logical source paths, roles, byte sizes, and SHA-256 hashes.
- `validation_report.json`: deterministic row/count/hash checks for all generated artifacts and copied frozen manifests.

The auxiliary city names come from `ucdb_city_lookup_for_event_anatomy.csv`; the builder requires all 94 IDs to match and checks candidate versus lookup coordinates to within `1e-9` degrees. Names do not affect sample selection or analysis. A minimal, five-column, 94-row package-local subset is written to `04_PROTOCOLS/frozen_inputs/AUXILIARY_UCDB_94_CITY_LOOKUP.csv` for later self-contained regeneration; it is an auxiliary join artifact, not a prospective design manifest.

## Regeneration

From the private reviewer-repository root:

```bash
python3 05_CODE/scripts/build_si_evidence_tables.py \
  --source-root . \
  --name-lookup 04_PROTOCOLS/frozen_inputs/AUXILIARY_UCDB_94_CITY_LOOKUP.csv
```

The private reviewer repository includes the frozen processed-source closure required by the builder. The manuscript handoff package may instead point `--source-root` to the separately retained immutable research workspace.

The script uses no random operations. It enforces the frozen grid rule (at least 3 core and 10 ring pixels) and transition rule (at least 2 observed hours in each of sunset hours -3 to -1 and +4 to +6). Relevant prospective selection and model manifests are copied byte-for-byte to `04_PROTOCOLS/frozen_inputs/`.

When `--name-lookup` is omitted and the external full lookup is unavailable, the builder automatically uses the package-local `04_PROTOCOLS/frozen_inputs/AUXILIARY_UCDB_94_CITY_LOOKUP.csv`.

In `source_provenance_manifest.csv`, `reviewer_repository`, `manuscript_package`, and `original_workspace` are logical root labels: each associated relative path is resolved beneath the appropriate package or directory supplied through `--source-root`. Historical absolute strings retained in immutable manifests are non-operative provenance. Obsolete GRL manuscript files were not used.
