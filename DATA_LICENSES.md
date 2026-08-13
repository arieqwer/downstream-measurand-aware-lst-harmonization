# Data and code licenses

The original code written for this reproducibility package is licensed under the MIT License; see [LICENSE](LICENSE).

Derived tables and retained processed evidence from NOAA GOES ABI products and the European Commission's GHS-UCDB remain subject to the terms and attribution requirements of their upstream providers. Inclusion in this reviewer package does not relicense upstream data. No raw provider files are redistributed.

The 94-row auxiliary city lookup in `04_PROTOCOLS/frozen_inputs/AUXILIARY_UCDB_94_CITY_LOOKUP.csv` is included only to make the city-name join reproducible. It was not used to select the prospective cohort or fit a model.
