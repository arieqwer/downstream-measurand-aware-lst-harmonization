# Metric-aware GOES harmonization reproducibility

## Scientific sequence

1. `MULTIPLATFORM_HARMONIZATION_PROTOCOL.md` was frozen before the first GOES-19 correction was evaluated.
2. `scripts/run_multiplatform_harmonization.py --stage derive` selected and serialized the 2022-2024 GOES-18/16 model without reading the 2025 holdout.
3. `scripts/run_multiplatform_harmonization.py --stage validate` opened the 2025 GOES-18/19 holdout once.
4. `MULTIPLATFORM_EXPANDED_VALIDATION_PROTOCOL.md` was frozen before GOES-18 was extracted for 43 additional western cities.
5. `GOES18_GOES19_METRIC_AWARE_HARMONIZATION_PROTOCOL.md` and the eight 2026 windows were frozen before either 2026 platform was extracted.
6. `scripts/train_goes18_goes19_metric_harmonization.py` selected and serialized the 2025 sensor-pair-specific models.
7. `scripts/validate_goes18_goes19_metric_harmonization_2026.py` opened the independent 2026 holdout without refitting.

## Principal rebuild commands

Run from the project root with `PYTHONPATH=scripts` where shown.

```bash
PYTHONPATH=scripts python3 scripts/run_multiplatform_harmonization.py --stage derive
PYTHONPATH=scripts python3 scripts/run_multiplatform_harmonization.py --stage validate
PYTHONPATH=scripts python3 scripts/run_expanded_harmonization_validation.py --stage historical
PYTHONPATH=scripts python3 scripts/run_expanded_harmonization_validation.py --stage validation
PYTHONPATH=scripts python3 scripts/run_expanded_harmonization_validation.py --stage combine
PYTHONPATH=scripts python3 scripts/train_goes18_goes19_metric_harmonization.py
PYTHONPATH=scripts python3 scripts/validate_goes18_goes19_metric_harmonization_2026.py
PYTHONPATH=scripts python3 scripts/analyze_harmonization_error_cascade.py
PYTHONPATH=scripts python3 scripts/build_metric_harmonization_synthesis.py
PYTHONPATH=scripts python3 scripts/validate_metric_harmonization_package.py
```

The extraction commands use `scripts/extract_goes_sunset_trajectories.py`, the frozen city and interval files in each data directory, and the public NOAA `noaa-goes18` or `noaa-goes19` S3 bucket. Raw satellite files are streamed and are not redistributed; extracted city-unit summaries and source-key inventories retain provenance.

## Randomness

All model and bootstrap seeds are fixed at `20260810`. Crossed folds are deterministic functions of longitude rank and event order. Model manifests contain protocol, input and serialized-model SHA-256 hashes.

## Validation

`scripts/validate_metric_harmonization_package.py` checks frozen hashes, holdout dates, sample counts, scan-time tolerances, finite physical values, the exact error-variance identity, prospective uncertainty criteria and figure exports. It writes `metric_harmonization_validation.json` on success.

## Scope

The processed package supports the GOES-18/GOES-16 and GOES-18/GOES-19 clear-sky urban comparison in the tested North American common domain. It does not provide a physical angular correction or support extrapolation to other satellite products without new validation.
