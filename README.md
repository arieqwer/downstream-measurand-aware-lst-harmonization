# Measurand-aware GOES land surface temperature harmonization

**Public test release v2.1.2-r0 — 2 November 2026.** This package contains the revised analysis code, processed inputs, fitted models, figures, and clean manuscript/Supplementary Information for author review. It is a prerelease. The final release **v2.1.2-r1 has not been published** and requires separate author confirmation. Earlier releases remain available as historical versions; this is the current test package.

The study assesses inter-platform consistency at the downstream scientific quantity. It compares urban-core and surrounding-ring temperatures, their spatial contrast, and the contrast's change across sunset. The final 2026 evaluation uses the same 75 cities as 2025 calibration and is a post hoc temporal evaluation. Fitting, selection and residual-interval calibration use calibration data only.

## Main findings and scope

Across five evaluation cohorts and three GOES platform pairings, component RMSE decreased by 29.3–59.7%, while contrast RMSE ranged from an 11.5% reduction to a 13.1% increase. The 2026 contrast change remains uncertain. Directional sign support applies to 31.9% of transitions; the expansion subgroup fails both fixed directional criteria, and the original subgroup exceeds the coverage band.

The independent three-station SURFRAD comparisons assess raw satellite products at station scale. Full urban core/ring workflow ground validation remains incomplete. The covariance decomposition is statistical accounting, not unique physical causal attribution. Strict-DQF sensitivity is restricted to three retained cities; sampled cloud diagnostics cover selected acquisitions on eight days. The June-only GOES-17 comparison does not isolate LHP effects. Generalization of the final selector to entirely unseen cities remains untested.

## Repository organization

Existing folder names are preserved, with revised contents:

- `02_EVIDENCE/`: current numerical results, exact MSE budgets, bootstrap outputs, fitted models/predictions, provenance, native/quality/cloud diagnostics and station benchmarks.
- `03_PROTOCOLS/`: dated original design protocols and a status explanation. Current post hoc interpretation supersedes earlier prospective terminology; the dated protocols remain source history.
- `04_CODE/`: source-extraction and diagnostic drivers. Raw-provider reconstruction is a separate reproduction level.
- `05_CODE/`: traced figure-building functions used by the portable entry points.
- `06_SUBMISSION/`: current clean manuscript and SI snapshots for this test version; no reviewer reports or response letters.
- `data/`: corrected processed regional inputs, source projection metadata, basemaps and retained decoded native map arrays.
- `outputs/figures/`: six current main figures. Regeneration writes to a separate output directory.
- `scripts/`: portable fitting/evaluation, tables, figures, station reconstruction and independent verification.

Start with [DATA_DIAGNOSTICS_INDEX.md](DATA_DIAGNOSTICS_INDEX.md) for exact evidence filenames and [REVIEWER_DIAGNOSTICS.md](REVIEWER_DIAGNOSTICS.md) for the requested physical and quality dimensions. The SI contains five tables and no Notes. Its CSV mirrors are `02_EVIDENCE/si_tables/Table_S1_publication.csv` through `Table_S5_publication.csv`. Other repository tables are computational evidence, not additional SI attachments.

## Reproduce the processed-data analysis

The recorded full processed-data reproduction used Python 3.9.6 in a new virtual environment without inherited site packages. Direct dependencies and the complete tested environment are pinned in `requirements.txt`, `requirements-lock.txt` and `environment.yml`. Create the environment with a compatible Python 3.9 interpreter:

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

## Verification and provenance

`02_EVIDENCE/reproducibility/` records the fresh twelve-stage processed-data reproduction executed for this test release: 1,110 independent assertions and 4,137,623 numerical cells passed, all six regenerated figures matched pixelwise, and the separate quality and modern station checks passed. The existing isolated pinned Python environment was reused; a new environment installation is not claimed. Dated historical execution records are distinguished from these new results. Figure 1 uses fixed design/cartographic assets; Figures 2–5 use computational result tables; Figure 6 uses retained decoded native LST arrays. Figure regeneration does not re-download or re-decode raw provider files.

Bulk GOES/cloud grids and SURFRAD ASCII source files are not all redistributed. Exact object names, URLs, hashes, quality rules and missingness records identify the external sources. Source extraction needs provider inputs and the separate raw-format environment. Ground-emissivity sensitivity does not perturb actual ABI retrieval inputs. See [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md), [DATA_LICENSES.md](DATA_LICENSES.md) and [REPRODUCIBILITY_IMPLEMENTATION.md](REPRODUCIBILITY_IMPLEMENTATION.md).

Run `python3 scripts/verify_package.py` to check every packaged file without third-party dependencies. `MANIFEST.json` and `SHA256SUMS.txt` inventory this test package. [RELEASE_NOTES.md](RELEASE_NOTES.md) describes the changes. The repository manuscript copy cites v2.1.2-r0; local editorial master documents remain separate. No DOI is assigned to this test release.
