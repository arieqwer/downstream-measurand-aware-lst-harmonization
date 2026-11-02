# Covariance-regime stress test

This directory is deliberately separate from the frozen satellite evidence. It
contains a deterministic, bounded enumeration of the exact downstream MSE
identity and the five empirical cohort positions read from the frozen point
budget table.

Run from the manuscript-package root:

```bash
python3 05_CODE/scripts/build_covariance_regime_stress_test.py
```

The script generates:

- `covariance_regime_grid.csv`: correlation-plane summaries after enumerating
  component residual-SD ratios and differential-bias gains;
- `empirical_cohort_positions.csv`: empirical correlations, scale ratios and
  exact budget coordinates;
- `covariance_regime_simulation_summary.json`: complete grid definition and
  enumeration counts; and
- `covariance_regime_validation.json`: algebraic and output validation checks.
- `simulation_artifact_hashes.json`: SHA-256 hashes for the script, frozen input
  table and generated artifacts.

The corresponding PNG, PDF and SVG figure and caption are written to
`03_FIGURES/`. No random sampling, model fitting or new satellite observation is
used.
