# GOES evening-transition reproducibility

The pilot city and interval selection was written to `GOES_SUNSET_CONFIRMATORY_PROTOCOL.md`. The independent city holdout was frozen in `GOES_SUNSET_HELDOUT_CONFIRMATION_PROTOCOL.md` before its hourly temperature outcomes were extracted. Pilot and held-out cities do not overlap.

## Inputs

- GOES-16 ABI Level-2 CONUS land-surface temperature (`ABI-L2-LSTC`), downloaded from NOAA's public object store.
- Fixed city polygons and 10–20 km rings prepared from the existing urban panel.
- Precomputed 8-day hydroclimatic severity and city-specific true-night heat indicators.

GOES is a clear-sky surface-temperature product. The analysis does not infer all-sky air temperature or turbulent flux directly.

## Core commands

```bash
python3 scripts/analyze_goes_sunset_mechanism.py \
  --data-dir data/goes_sunset_pilot \
  --output-dir outputs/goes_sunset_mechanism

python3 scripts/analyze_goes_sunset_mechanism.py \
  --data-dir data/goes_sunset_confirmation \
  --output-dir outputs/goes_sunset_confirmation

python3 scripts/combine_goes_sunset_cohorts.py
python3 scripts/analyze_goes_evening_crossover.py
python3 scripts/run_goes_hydroclimate_decomposition.py
python3 scripts/build_goes_evening_transition_figure.py
python3 scripts/validate_goes_research_package.py
```

The extraction script is `scripts/extract_goes_sunset_trajectories.py`. Re-extraction requires network access to the NOAA archive and is substantially slower than rebuilding the analyses from the retained hourly parquet files.

## Determinism and validation

Bootstrap analyses use the fixed seed in `scripts/analyze_goes_sunset_mechanism.py` and in the evening-crossover script. `scripts/validate_goes_research_package.py` fails if source counts, city-hour uniqueness, physical LST ranges, pilot/holdout separation, focal confidence-interval direction, or required artifacts change. Its machine-readable output is `outputs/GOES_VALIDATION_REPORT.json`.

The package was last verified with Python 3.9.6 and the versions in `requirements_goes.txt`. A supported Python release should be used for future clean environments because Python 3.9 is end-of-life.
