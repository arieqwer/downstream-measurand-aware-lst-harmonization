# Measurand-aware GOES land surface temperature harmonization

Supporting numerical evidence for *Measurand-Aware Inter-Platform Consistency Assessment of GOES Land Surface Temperature Harmonization*.

Start with the tables below. The repository contains the full-precision results and targeted diagnostics that complement the manuscript and five-table SI. The optional [reproducibility kit](https://github.com/arieqwer/downstream-measurand-aware-lst-harmonization/releases/download/v2.1.3-r1/reproducibility-v2.1.3-r1.zip) contains the required processed inputs, fitted models and runnable code; it excludes duplicate outputs and unused extraction/debugging files.

## Find a result

| Question | Files |
| --- | --- |
| Do component improvements transfer to the contrast? | [Cohort performance](results/cohort_performance.csv), [exact MSE budgets](results/exact_mse_budgets.csv) |
| Which processing actions were selected? | [Model selection](results/model_selection.csv), [historical hour offsets](results/historical_hour_offsets.csv) |
| How uncertain are the 2021 and 2026 results? | [2021 intervals](results/uncertainty_2021.csv), [2026 intervals](results/uncertainty_2026.csv), [2021 interval influence](results/interval_influence_2021.csv) |
| How do directional results vary by cohort and period? | [Directional performance](results/directional_performance.csv) |
| How does covariance change across hours and viewing angles? | [Covariance partition](results/covariance_partition.json), [hour diagnostics](results/hour_diagnostics.csv), [view-angle diagnostics](results/view_angle_diagnostics.csv) |
| How sensitive are the findings to the July exclusion and signal scale? | [June-only sensitivity](results/june_sensitivity.csv), [observed contrast scale](results/contrast_scale.csv) |
| How do quality flags and cloud screening affect support and errors? | [Quality metrics](results/quality_sensitivity.csv), [retained support](results/quality_support.csv), [paired uncertainty](results/quality_uncertainty.csv), [cloud sensitivity](results/cloud_sensitivity.csv) |
| What retrieval metadata were available? | [Retrieval catalog](results/retrieval_metadata.csv), [quality categories](results/quality_categories.csv) |
| What did independent station comparisons show? | [2021 metrics](results/station_metrics_2021.csv), [2025–2026 metrics](results/station_metrics_2025_2026.csv), [uncertainty](results/station_uncertainty.csv), [ground assumptions](results/station_ground_sensitivity.csv), [neighborhood sensitivity](results/station_neighborhood_sensitivity.csv) |

CSV files can be viewed directly on GitHub or downloaded. `python3 verify.py` checks file integrity, table readability and exact MSE-budget closure using the Python standard library.

## Trace the city cohorts

[Candidate metadata](cohorts/candidate_city_metadata.csv) records city identifiers, coordinates, inherited group labels and candidate/retained membership at each stage. [Interval chronology](cohorts/interval_chronology.csv) identifies the observation windows. The [parent inventory](cohorts/parent_city_inventory.csv) preserves all 5,541 retained cities and their MODIS observation-support grouping; [pilot identifiers](cohorts/pilot_cities.csv) preserve the 60-city exclusion list used for the original higher-support cohort.

The parent inventory was constructed from 11,422 GHS-UCDB R2024A urban centres. Its grouping variable is the 2003–2025 mean available daytime MODIS LST pixel count with NDVI > 0.30 in the surrounding 10–20-km ring. The global median is 897.66 pixels; higher/lower support describes observation availability. The kit retains the upstream selection scripts and their covariate inputs. These historical provenance scripts describe the inherited selection; the offline analysis starts from the retained processed observations.

## Reproduce the analysis

Download and extract the [kit](https://github.com/arieqwer/downstream-measurand-aware-lst-harmonization/releases/download/v2.1.3-r1/reproducibility-v2.1.3-r1.zip). Its README gives the fitting, evaluation, table, figure and station commands. Models and selection rules use calibration data only. Numerical analysis files are unchanged by the repository reduction.

The tested scientific environment is Python 3.9.6. [requirements-lock.txt](requirements-lock.txt) restores the complete recorded 45-package environment; [requirements.txt](requirements.txt) lists the direct dependencies. Create it with:

```bash
python3.9 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

Alternatively, `conda env create -f environment.yml` uses the same lockfile through the pip section of [environment.yml](environment.yml). [manifest.json](manifest.json) supplies file checksums.

## Interpretation and source data

The primary assessment is inter-platform consistency. The 2026 results are a post hoc temporal evaluation at the same 75 calibration cities. Strict-DQF findings concern only three cities, 215 hourly observations and 21 transitions; the sampled cloud checks do not cover complete periods or transitions. Station comparisons assess raw satellite pixels, without validating the complete urban core–ring workflow. The covariance decomposition and available diagnostics do not uniquely identify physical causes. Unfavorable contrast and directional subgroup findings are retained in the linked tables.

ERA5-Land: [Copernicus Climate Data Store](https://doi.org/10.24381/cds.e2161bac) and Earth Engine `ECMWF/ERA5_LAND/HOURLY` / `ECMWF/ERA5_LAND/DAILY_AGGR`. GOES LST/cloud products: NOAA archives `ABI-L2-LSTC` / `ABI-L2-ACMC`. SURFRAD: NOAA Global Monitoring Laboratory. GHS-UCDB: [R2024A](https://doi.org/10.2905/JRC.05RDPR0); NOAA LST metadata: [dataset record](https://doi.org/10.7289/V52R3PZ8). Exact retained satellite/ground source manifests accompany the kit. Bulk raw-provider files are not bundled.

Original code is under the [MIT license](license). Processed NOAA, GHS-UCDB and basemap materials retain their upstream terms and attribution; this repository does not relicense them. Earlier releases remain accessible from the release history.
