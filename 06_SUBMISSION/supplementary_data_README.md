# Machine-readable supplementary data

The `Supplementary_Data_S1-S15.zip` archive accompanies “Measurand-Aware Validation of Cross-Platform GOES Land Surface Temperature Harmonization.” It contains exactly the 15 numbered machine-readable files listed, with package-relative paths and dimensions, in Table S12 of the Supplementary Materials.

Contents include:

- fixed 94-city candidate metadata and 57-interval chronology;
- cohort/event attrition and full model-selection tables;
- observed cross-cohort RMSE and exact MSE-decomposition tables;
- 2021 external-replication bootstrap and influence summaries;
- 2026 crossed-bootstrap and residual-interval outputs;
- source-provenance and validation reports.

The SI table builder (`04_CODE/scripts/build_si_evidence_tables.py`), covariance stress-test builder (`04_CODE/scripts/build_covariance_regime_stress_test.py`), fixed inputs, full workflow protocols, and top-level `SHA256SUMS.txt` remain in the parent reproducibility repository; they are not ZIP members.

These files quantify inter-platform consistency. GOES platforms are consistency references, not ground truth. The city-name lookup is auxiliary and did not enter sample selection or fitted models. Country and population fields were not present in the frozen supplied metadata and are therefore not imputed here.
