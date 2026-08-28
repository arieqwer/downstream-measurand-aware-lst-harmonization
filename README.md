# Measurand-aware GOES LST harmonization

This is the private peer-review reproducibility repository for the *Remote Sensing* article **“Measurand-Aware Validation of Cross-Platform GOES Land Surface Temperature Harmonization”** by Shiyu Li and Shuanggen Jin.

The study asks whether corrections that improve two component land-surface-temperature measurements also improve the spatial difference and temporal change used for inference. It uses frozen GOES-16/17/18/19 evaluation cohorts, exact mean-squared-error decomposition, a measurand-specific correction selector, a residual-interval rule, and a deterministic covariance-regime stress test.

## Reproducibility scope

This repository contains frozen processed source tables, manifests, row-level prediction outputs, machine-readable supplementary data, and deterministic scripts needed to regenerate every main/SI figure, supplementary table, and reported numerical summary. It is not a raw-to-product reprocessing archive. Re-extraction and refitting from upstream satellite products require the larger internal analysis environment and are outside this reviewer package.

Raw provider files are not redistributed. Upstream availability and licensing are summarized in [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md) and [DATA_LICENSES.md](DATA_LICENSES.md). Historical absolute paths retained inside frozen JSON manifests are non-operative provenance strings; the commands below use repository-relative paths.

## Contents

- `02_EVIDENCE/`: frozen point estimates, bootstrap draws, replication evidence, simulation outputs, and submission-table sources.
- `03_FIGURES/`: main figures and captions in submission and vector formats.
- `04_PROTOCOLS/`: frozen protocols, manifests, and the package-local 94-city auxiliary lookup.
- `05_CODE/scripts/`: deterministic builders and the independent reviewer validator.
- `05_CODE/tests/`: tests for the reusable MSE-decomposition module.
- `data/` and `outputs/`: the 40-file processed-source closure required to rebuild the SI evidence tables and validate all reported five-cohort summaries.
- `07_SUBMISSION/`: the deterministic machine-readable supplementary-data archive and its README.
- `docs/`: claim-to-evidence mapping, terminology, and claim boundaries.

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

That command rebuilds the SI evidence tables, deterministic covariance grid, Figures 1–4, the machine-readable SI ZIP, and then runs the independent numeric validator and unit tests. Figure 2 is the cross-cohort synthesis, and Figure 3 is the covariance-regime stress test.

For a read-only numerical audit without rebuilding artifacts:

```bash
python 05_CODE/scripts/validate_reviewer_package.py
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

## Review access and citation

The repository is private during peer review. The corresponding author can grant access to the handling editor or designated reviewers. A versioned public archive with a permanent identifier will be released upon acceptance. Citation metadata are in [CITATION.cff](CITATION.cff).

Correspondence: Shuanggen Jin, `sgjin@hpu.edu.cn`.
