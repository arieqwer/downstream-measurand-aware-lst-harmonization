# Hydroclimatic controls on urban core-ring thermal decay

This private reproducibility package contains the compact processed outputs and code needed to regenerate every main and supplementary display item, export the eight supplementary-table source files, and verify the principal numerical results.

The analysis evaluates how paired daytime-to-nighttime land-surface-temperature decay differs between urban cores and 10-20 km rings under moist-low-demand, dry-high-demand, and extreme dry-high-demand states. It also tests built-form heat storage, long-term water support, stress duration, post-stress memory, and secondary cross-city concurrence.

## Contents

- `data/processed/analysis_outputs/`: final model summaries and sensitivity outputs.
- `data/processed/figure_source_data/`: compact city/state and plotting source tables.
- `data/processed/city_covariates.csv`: city-level matching and vegetation-support variables.
- `data/processed/urban_form_covariates.csv`: built-form and external-process covariates.
- `scripts/make_upgrade_figures.py`: generates Figures 1-4.
- `scripts/make_upgrade_supplementary_figures.py`: generates Figures S1-S5.
- `scripts/export_supplementary_tables.py`: exports source data for Tables S1-S8.
- `scripts/validate_key_results.py`: checks the headline estimates against archived outputs.
- `scripts/analysis/`: transparent analysis code for rerunning the principal models when the access-controlled interval panels are available.

Rendered figures are intentionally excluded. Generated files are written under the ignored `outputs/` directory.

## Reproduce displays and tables

Python 3.10 or newer is recommended. Create an environment with `requirements.txt` or `environment.yml`, then run:

```bash
bash scripts/run_all.sh
```

Outputs are written to:

```text
outputs/figures/main/
outputs/figures/supplementary/
outputs/tables/
```

The display-item workflow uses only the compact files committed here. The principal analysis scripts additionally require the access-controlled files described in `data/README.md`.

## Key definitions

- **Dry-high-demand (DHD):** low root-zone soil-moisture percentile and high vapor-pressure-deficit percentile.
- **True-night heat:** city-specific 2 m air-temperature exceedance during 22:00-06:00 local solar time.
- **Apparent thermal decay:** logarithmic daytime-to-nighttime LST ratio divided by the nominal 12 h Terra overpass separation.
- **Differential apparent decay:** apparent decay in the urban core minus apparent decay in its ring. Positive values indicate faster apparent core decay; negative values indicate slower apparent core decay.
- **Severe day/night inversion:** daytime core-minus-ring anomaly below -0.25 degrees C and nighttime anomaly above +0.25 degrees C.

The apparent-decay metric is an endpoint diagnostic from paired MOD11A2 composites, not a continuously observed cooling-rate curve. Population quantities are static-weight represented-panel counts, not estimates of unique people or global population at risk.

## License

Code is released under the MIT License. Processed outputs retain any attribution or reuse constraints imposed by their upstream data providers.
