# Downstream-metric framework reproducibility

## Environment

- Python 3.9.6
- NumPy 2.0.2
- pandas 2.3.3
- Matplotlib 3.9.4
- PyArrow 21.0.0

Additional dependencies are listed in `requirements_goes.txt`.

## Frozen inputs

- `DOWNSTREAM_METRIC_AWARE_HARMONIZATION_PROTOCOL.md`
- `GOES17_GOES16_EXTERNAL_METRIC_REPLICATION_PROTOCOL.md`
- `data/goes16_2019_2021_external_metric/FROZEN_SELECTION.json`
- `data/goes17_2019_2021_external_metric/FROZEN_SELECTION.json`

The manifests store hashes for the protocol, fixed cities, fixed intervals, geometry and source 2026 cohort.

## External extraction

The retained hourly summaries can be regenerated from the public NOAA GOES archives with:

```bash
python3 scripts/extract_goes_sunset_trajectories.py \
  --data-dir data/goes16_2019_2021_external_metric \
  --bucket noaa-goes16 \
  --cities-file goes_sunset_cities.csv \
  --intervals-file goes_sunset_intervals.csv

python3 scripts/extract_goes_sunset_trajectories.py \
  --data-dir data/goes17_2019_2021_external_metric \
  --bucket noaa-goes17 \
  --cities-file goes_sunset_cities.csv \
  --intervals-file goes_sunset_intervals.csv
```

Raw satellite files are streamed and are not redistributed. The retained summaries contain source keys and timestamps.

## Analysis order

```bash
python3 scripts/analyze_downstream_metric_framework.py
python3 scripts/run_goes17_goes16_external_metric_replication.py
python3 scripts/synthesize_downstream_metric_framework.py
python3 scripts/build_downstream_metric_framework_figure.py
python3 -m unittest discover -s tests -p 'test_metric_aware_harmonization.py' -v
python3 scripts/validate_downstream_metric_framework.py
```

The external analysis uses 5,000 crossed city-event bootstrap draws with seed `20260810`. The external correction is a fixed hour-from-sunset mean offset fitted separately for core and ring using only the four 2019–2020 calibration intervals.

## Validation gates

- Point and bootstrap MSE-budget closure below `1e-10 K^2`.
- Five out-of-sample evaluation cohorts present.
- Exactly 5,000 bootstrap draws per scope in 2021 and 2026.
- External input and protocol hashes match their frozen manifests.
- Core and ring improve and covariance-loss penalty is positive in every external 2021 event.
- PNG, PDF and SVG synthesis figures exist with source CSV files.
- No manuscript or supporting-information file is copied into the research outputs.

The final machine-readable audit is `outputs/grl_deepening_2026/downstream_metric_framework/downstream_metric_framework_validation.json`.
