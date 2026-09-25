# Measurand-aware GOES LST harmonization

This is the reproducibility repository for the article **“Measurand-Aware Validation of Cross-Platform GOES Land Surface Temperature Harmonization”**.

The study asks whether corrections that improve two component land-surface-temperature measurements also improve the spatial difference and temporal change used for inference. It uses frozen GOES-16/17/18/19 evaluation cohorts, exact mean-squared-error decomposition, a measurand-specific correction selector, a residual-interval rule, and a deterministic covariance-regime stress test.

## Reproducibility scope

This repository contains frozen processed source tables, manifests, row-level prediction outputs, supplementary data, and deterministic scripts needed to regenerate every main/SI figure, supplementary table, and reported numerical summary. 

Raw provider files are not redistributed. Upstream availability and licensing are summarized in [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md) and [DATA_LICENSES.md](DATA_LICENSES.md). 

## Contents

- `02_EVIDENCE/`: frozen point estimates, bootstrap draws, replication evidence, simulation outputs, and submission-table sources.
- `03_PROTOCOLS/`: frozen protocols, manifests, and the package-local 94-city auxiliary lookup.
- `04_CODE/scripts/`: deterministic builders and validator.
- `05_CODE/tests/`: tests for the reusable MSE-decomposition module.
- `data/` and `outputs/`: the 40-file processed-source closure required to rebuild the SI evidence tables and validate all reported five-cohort summaries.
- `06_SUBMISSION/`: the deterministic supplementary-data archive and its README.

## Environment

Python 3.11 is recommended. Create an isolated environment and install the pinned review dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r 05_CODE/requirements_goes.txt
```

## One-command reproduction

From the repository root:

```bash
bash scripts/run_all.sh
```

That command rebuilds the SI evidence tables, deterministic covariance grid, Figures 1–5, the machine-readable SI ZIP, and then runs the independent numeric validator and unit tests. Figure 3 is the cross-cohort synthesis, and Figure 4 is the covariance-regime stress test.

For a read-only numerical audit without rebuilding artifacts:

```bash
python 04_CODE/scripts/validate_reviewer_package.py
python -m unittest discover -s 05_CODE/tests -p 'test_metric_aware_harmonization.py' -v
shasum -a 256 -c SHA256SUMS.txt
```

The validator independently reconstructs all 15 hourly RMSE rows and 10 hourly/transition MSE decompositions from retained row-level predictions, verifies exact-identity closure, checks the 2026 residual-interval results, audits both 5,000-draw crossed-bootstrap archives, and verifies the source-provenance manifest.

## Main validated results

- Core and ring RMSE decreased by 29.3–60.0% across all five evaluation cohorts.
- Core–ring contrast RMSE ranged from a 12.5% deterioration to an 11.3% improvement.
- Positive covariance-loss penalties offset 94.6–113.6% of gross variance-plus-bias gains.
- In the prospective 2026 holdout, the residual-interval rule covered 529/588 transitions, excluded zero for 180/588 cases, and 174/180 supported signs agreed with the GOES-18 reference-platform sign.
- The deterministic stress test enumerates 11,612,160 bounded configurations across 9,216 correlation cells.

GOES-18 is a consistency reference in the 2026 comparison, not ground truth; reference-sign agreement is not absolute LST accuracy.
