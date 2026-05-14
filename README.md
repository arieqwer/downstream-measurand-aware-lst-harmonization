# Urban green-refuge reliability during dry hot nights

This repository is a curated reproducibility package for a *Nature Cities* submission. It is intentionally not the full working directory. It contains processed source data and scripts needed to regenerate the display items, source tables, and key reported numerical results from processed data.

## What is included

- `data/processed/metadata/`: compact city metadata and retained-panel summaries used by the plotting scripts.
- `data/processed/extended_outputs_local/`: processed analysis summaries used as source data for figures, tables, and key results.
- `data/source_tables/`: source tables as CSV files.
- `scripts/`: scripts that regenerate display items, source tables, and a key-results check from the processed data.

## What is excluded

Raw satellite/climate products and large upstream intermediate panels are excluded. These include Google Earth Engine exports, ERA5/ERA5-Land extraction products, full MODIS/urban panel files, and multi-GB analysis panels. Those files are not required to reproduce the display items and source tables from the processed source data included here.

The excluded upstream products come from public or third-party data providers and should be obtained from their original sources under the corresponding licenses.

## Reproduce the figures and tables

Create a Python environment using either `requirements.txt` or `environment.yml`, then run:

```bash
python scripts/make_main_and_selected_supplementary_figures.py
python scripts/make_figure_5_reliability_pathway.py
python scripts/make_supplementary_figures_s1_s2.py
python scripts/make_supplementary_figure_s7_robustness.py
python scripts/export_supplementary_tables.py
python scripts/validate_key_results.py
```

Generated files are written to:

- `outputs/figures/main/`
- `outputs/figures/supplementary/`
- `outputs/tables/`

## Script-to-output map

- `make_main_and_selected_supplementary_figures.py`: display items generated from the processed analysis summaries.
- `make_figure_5_reliability_pathway.py`: main Figure 5 from the reliability-pathway source tables.
- `make_supplementary_figures_s1_s2.py`: additional display items.
- `make_supplementary_figure_s7_robustness.py`: robustness display item.
- `export_supplementary_tables.py`: source tables as Markdown tables.
- `validate_key_results.py`: prints key numerical findings from processed source tables.

## Notes for review and reuse

Population quantities are represented-panel burdens, not global population-at-risk estimates. Counterfactual pathway summaries are association-based standardizations under fitted models and are not intervention simulations.
