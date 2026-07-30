# Data layout

## Committed processed data

`processed/analysis_outputs/` contains the final statistical summaries used by the plotting, table-export, and validation scripts. `processed/figure_source_data/` contains compact plotting tables, including the city-location data used for the global map. The two city-level covariate files support matching and built-form interpretation.

The processed outputs preserve unrounded model estimates so that displayed values and reported summaries can be regenerated without numerical loss.

## Access-controlled analysis inputs

The scripts under `scripts/analysis/` expect the following files under the git-ignored `data/external/` directory:

| File | Role |
| --- | --- |
| `valid_city_interval_panel.parquet` | Complete-case city-by-8-day panel used for principal decay, distributional, transition, duration, post-stress, and concurrence models |
| `dhd_stress_history_panel.parquet` | DHD indicator history used to construct run length and post-stress lag variables |
| `alt_ring_gradient_panel.parquet` | Alternative 5-15 km, 10-20 km, and 20-30 km ring sensitivity panel |

These files are excluded from GitHub because of size and can be supplied through an access-controlled review archive. They are not needed to regenerate the figures or supplementary-table source files from the committed processed outputs.

## Provenance notes

- MOD11A2 Collection 6.1 daytime and nighttime 8-day LST composites provide paired endpoints. The original extraction retained native valid LST pixels and did not apply additional `QC_Day` or `QC_Night` bit filtering.
- GHS-BUILT-S values greater than 0.20 square meters of built surface per 100 m source cell define built presence before aggregation to MODIS support pixels. The criterion is a built-presence threshold.
- A MOD13A2 NDVI threshold greater than 0.30 defines vegetation-associated support.
- City-intervals with missing core–ring thermal outcomes are excluded before continuous outcomes and event indicators are constructed.
