# Claim boundaries

## Claims the paper can make

- Harmonization success is measurand dependent.
- Stronger agreement for component products does not guarantee stronger agreement for their derived spatial contrast or temporal transition.
- For a linear derived measurand, exact MSE decomposition can identify whether component variance and differential-bias gains exceed loss of beneficial error covariance.
- Frozen out-of-sample validation can support different actions at different measurement levels: correct, retain raw, or abstain.
- The same covariance-loss mechanism appears across the tested GOES platform replacements and evaluation cohorts.
- Urban core–ring LST provides a concrete geospatial demonstration of the general workflow.

## Claims the paper must not make

- Do not call the MSE identity a new theorem or new covariance law.
- Do not claim the first covariance-aware Earth-observation harmonization method.
- Do not claim a new angular-normalization model.
- Do not claim that GOES-16, GOES-17, GOES-18, or GOES-19 is ground truth.
- Do not claim absolute LST accuracy; the outcome is inter-platform consistency.
- Do not call all five cohorts independent temporal replications. Some spatial cohorts share event dates.
- Do not call the 2021 replication prospective. It is frozen and outcome-blind but historical.
- Do not claim universal uncertainty calibration; the expansion cohort under-covered.
- Do not uniquely attribute discrepancies to view angle, emissivity, thermal anisotropy, atmospheric path, parallax, mixed pixels, or retrieval implementation.
- Do not infer that component correction causes a physical urban-temperature change.
- Do not generalize beyond clear-sky geostationary LST, the tested North American domain, platform pairs, and derived metrics without qualification.

## Required distinctions

- **Calibration**: data used to fit a fixed correction or choose an action.
- **Evaluation cohort**: data not used to fit that evaluated correction.
- **Prospective holdout**: the 2026 GOES-18/19 evaluation fixed before outcomes were opened.
- **Historical external replication**: the 2021 GOES-17/16 outcome-blind test, frozen before GOES-17 outcome extraction.
- **Component-derived metric**: construct the downstream metric after correcting its components.
- **Direct downstream correction**: fit or select correction using downstream loss itself.
- **Raw retention**: preserve the uncorrected downstream metric when correction has not demonstrated out-of-sample benefit.
- **Abstention**: withhold a directional statement when the frozen uncertainty interval includes zero.

## Preferred novelty statement

> We introduce and prospectively evaluate a downstream-measurand-aware harmonization workflow that propagates error covariance through derived geospatial quantities, accepts correction only when out-of-sample loss improves at the scientific metric, and otherwise retains the raw metric or abstains from directional inference.

## Avoided novelty statement

> We discover a new covariance mechanism or universally solve multisensor harmonization.
