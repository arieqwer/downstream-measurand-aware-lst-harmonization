# Implementation metadata

The study's primary model fitting and crossed city–interval bootstrap use seed 20260810. The modern station benchmark uses seed 20261029. Removing these implementation details from the manuscript does not remove them from the reproducibility record.

The tested processed-data environment used Python 3.9.6, NumPy 2.0.2, pandas 2.3.3, scikit-learn 1.6.1, Matplotlib 3.9.4 and PyArrow 21.0.0. See requirements.txt, requirements-lock.txt and environment.yml for the complete configuration. Fitted model objects are retained under 02_EVIDENCE/analysis_outputs. These paths and the relevant input manifests are indexed by DATA_DIAGNOSTICS_INDEX.md.

Core/ring fitting, model selection, and residual interval calibration use the designated calibration data only. The empirical 90th percentile uses the higher interpolation rule; replacing it with linear interpolation changes sign support. Raw provider inputs are documented through manifests and are not all redistributed.

This file records configuration; it is not a claim that tests were rerun during an editorial-only update. Executed scientific checks remain under 02_EVIDENCE/reproducibility.
