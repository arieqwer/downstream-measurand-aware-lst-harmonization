# Measurand-aware GOES land surface temperature harmonization

release v2.1.2-r1 — 3 November 2026
The study assesses inter-platform consistency at the downstream scientific quantity. This package contains the analysis code, processed inputs and fitted models for the study. 

## Repository organization
- `02_EVIDENCE/`: current numerical results, exact MSE budgets, bootstrap outputs, fitted models/predictions, provenance, native/quality/cloud diagnostics and station benchmarks.
- `03_PROTOCOLS/`: dated original design protocols and a status explanation. Current post hoc interpretation supersedes earlier prospective terminology; the dated protocols remain source history.
- `04_CODE/`: source-extraction and diagnostic drivers. Raw-provider reconstruction is a separate reproduction level.
- `05_CODE/`: traced figure-building functions used by the portable entry points.
- `data/`: corrected processed regional inputs, source projection metadata, basemaps and retained decoded native map arrays.
- `scripts/`: portable fitting/evaluation, tables, figures, station reconstruction and independent verification.

## Reproduce the processed-data analysis

The recorded full processed-data reproduction used Python 3.9.6 in a new virtual environment without inherited site packages. Direct dependencies and the complete tested environment are pinned in `requirements.txt` and `environment.yml`. Create the environment with a compatible Python 3.9 interpreter:

```bash
python3.9 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export PYTHONNOUSERSITE=1
.venv/bin/python scripts/reproduce.py --stages all
.venv/bin/python scripts/reproduce_tables.py
.venv/bin/python scripts/reproduce_figures.py
.venv/bin/python scripts/verify_reproduction.py
```

No provider downloads are needed for this processed-input level. Paths resolve from the package root, independently of the shell working directory. `LST_REPRODUCTION_OUTPUT` sets a separate writable output root. Candidates, folds, thresholds, seeds and hyperparameters remain fixed; no 2026 outcome is used for fitting or selection. Residual-interval calibration uses the empirical 90th percentile with the `higher` rule.

The modern station benchmark can be regenerated separately:

```bash
.venv/bin/python scripts/reproduce_modern_surface.py \
  --output-dir outputs/modern_reproduced \
  --verify-against 02_EVIDENCE/surface/modern
```

It retains 173 matched GOES-18/19 pairs in 2025 and 109 in 2026, sampled on the first local day of selected intervals at three sites. All retained GOES-19 station observations have DQF 1; no joint strict-DQF-0 pair was available. It does not apply city-trained corrections to station pixels.

For the restricted strict-quality analysis:

```bash
LST_NATIVE_WORKSPACE=outputs/native_checks \
  .venv/bin/python 04_CODE/quality/run_repaired_quality_sensitivity.py
```
