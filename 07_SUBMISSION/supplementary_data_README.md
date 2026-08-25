# Machine-readable supplementary data

This 25-member archive accompanies “Measurand-Aware Validation of Cross-Platform GOES Land Surface Temperature Harmonization.” Table S12 of the Supplementary Materials assigns Supplementary Data labels S1–S15 to the 15 numbered machine-readable artifacts and lists their roles and dimensions. The other ten members are archive-support files: two READMEs, two unnumbered summary/audit CSVs (`cohort_attrition_summary.csv` and `metric_aware_decision_audit.csv`), and six simulation provenance, validation, and source files under `02_EVIDENCE/simulation/`.

Contents include:

- fixed 94-city candidate metadata and 57-interval chronology;
- cohort/event attrition and full model-selection tables;
- observed cross-cohort RMSE and exact MSE-accounting tables;
- 2021 external-replication bootstrap and influence summaries;
- 2026 crossed-bootstrap and uncertainty-gate outputs;
- deterministic covariance-regime stress-test outputs;
- source-provenance and validation reports.

The SI table builder (`05_CODE/scripts/build_si_evidence_tables.py`), covariance stress-test builder (`05_CODE/scripts/build_covariance_regime_stress_test.py`), fixed inputs, full workflow protocols, and top-level `SHA256SUMS.txt` remain in the parent reproducibility package; they are not members of this 25-file archive.

These files quantify inter-platform consistency. GOES platforms are consistency references, not ground truth. The city-name lookup is auxiliary and did not enter sample selection or fitted models. Country and population fields were not present in the frozen supplied metadata and are therefore not imputed here.
