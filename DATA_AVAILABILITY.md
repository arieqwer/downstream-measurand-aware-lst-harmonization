# Data and code availability

The project repository is https://github.com/arieqwer/downstream-measurand-aware-lst-harmonization. The public prerelease **v2.1.2-r0** is the test package for author review: https://github.com/arieqwer/downstream-measurand-aware-lst-harmonization/releases/tag/v2.1.2-r0. The final v2.1.2-r1 release has not been published. No DOI is asserted.

This package includes corrected processed regional extracts, source/missingness manifests, fitted models, bootstrap outputs, numerical tables, figure inputs/code and raw-product station matchups. [DATA_DIAGNOSTICS_INDEX.md](DATA_DIAGNOSTICS_INDEX.md) maps the manuscript and five SI tables to exact evidence files. Clean manuscript/SI snapshots are in `06_SUBMISSION/`.

ERA5-Land inputs are available from the Copernicus Climate Data Store (https://doi.org/10.24381/cds.e2161bac) and Google Earth Engine collections `ECMWF/ERA5_LAND/HOURLY` and `ECMWF/ERA5_LAND/DAILY_AGGR`. NOAA cloud archives supply raw GOES products under `ABI-L2-LSTC` and `ABI-L2-ACMC`; exact source-object identifiers and hashes are retained in the request/native manifests. SURFRAD radiation data are supplied by NOAA Global Monitoring Laboratory; source URLs, station/date support and matching rules are retained with the station evidence. GHS-UCDB R2024A and NOAA LST metadata are identified by https://doi.org/10.2905/JRC.05RDPR0 and https://doi.org/10.7289/V52R3PZ8. Basemap source/license metadata accompany the cartographic inputs.

The package does not redistribute all bulk raw-provider files. Processed-data reproducibility and station-scale evidence do not establish independent ground validation of the full urban workflow. See `DATA_LICENSES.md` for upstream rights and attribution.
