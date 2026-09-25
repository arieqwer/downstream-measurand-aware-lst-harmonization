# Downstream-measurand framework reproducibility

## Environment

The analysis used Python 3.9.6. The package dependencies and recorded library
versions are pinned in `05_CODE/requirements_goes.txt`, including NumPy 2.0.2,
pandas 2.3.3, scikit-learn 1.6.1, Matplotlib 3.9.4, and PyArrow 21.0.0.

## Reproducibility scope

This repository contains the frozen processed-source closure used to rebuild
the design tables, figures, supplementary-data archive, and reported numerical
summaries. Raw provider files are not redistributed, and raw-data extraction is
outside the package-local rebuild.

The principal frozen protocols are:

- `03_PROTOCOLS/DOWNSTREAM_METRIC_AWARE_HARMONIZATION_PROTOCOL.md`;
- `03_PROTOCOLS/GOES17_GOES16_EXTERNAL_METRIC_REPLICATION_PROTOCOL.md`;
- the design-specific protocols under `03_PROTOCOLS/prior_frozen_designs/`;
- the corresponding selection and model manifests under
  `03_PROTOCOLS/frozen_inputs/`.

## One-command rebuild

From the repository root, run:

```bash
bash scripts/run_all.sh
```

The command rebuilds the deterministic SI evidence tables, covariance-regime
grid, Figures 1–5, and `06_SUBMISSION/Supplementary_Data_S1-S15.zip`. It then
runs the independent numerical validator and unit tests.

The constituent commands are:

```bash
python3 04_CODE/scripts/build_si_evidence_tables.py \
  --source-root . \
  --name-lookup 03_PROTOCOLS/frozen_inputs/AUXILIARY_UCDB_94_CITY_LOOKUP.csv
python3 04_CODE/scripts/build_remote_sensing_figures_1_2_3.py
python3 04_CODE/scripts/build_covariance_regime_stress_test.py \
  --preserve-approved-figure
python3 04_CODE/scripts/build_submission_figures.py
python3 04_CODE/scripts/build_supplementary_data_zip.py
python3 04_CODE/scripts/validate_reviewer_package.py
python3 -m unittest discover -s 05_CODE/tests \
  -p 'test_metric_aware_harmonization.py' -v
```

## Validation checks

The package-local validator:

- reconstructs 15 hourly RMSE rows across five stage-specific evaluation
  cohorts;
- reconstructs ten hourly/transition MSE decompositions;
- verifies exact-identity closure;
- checks the prospective 2026 residual-interval results;
- audits both 5,000-draw crossed city–interval bootstrap archives; and
- verifies every resolved entry in the source-provenance manifest.

The unit tests cover the linear-measurand identity, component/downstream
non-transfer, one-standard-error raw retention, and directional abstention.

The file-level integrity manifest is `SHA256SUMS.txt`; verify it with:

```bash
shasum -a 256 -c SHA256SUMS.txt
```

## Reproducibility boundary

GOES-18 is used as an inter-platform consistency reference in the 2026
comparison and is not treated as absolute ground truth. The repository supports
the reported processing-chain validation and does not claim to reconstruct
every upstream extraction or establish a universal GOES harmonization model.
