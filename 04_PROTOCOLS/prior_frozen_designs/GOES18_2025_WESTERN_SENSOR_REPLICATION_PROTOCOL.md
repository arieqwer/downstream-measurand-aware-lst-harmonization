# GOES-18 2025 Western Sensor Replication Protocol

Frozen before extraction or inspection of GOES-18 outcomes.

## Purpose

Distinguish 2025 event-regime heterogeneity from a GOES-19-specific instrument or retrieval effect by observing the same western cities, intervals and exposure definitions with GOES-18.

## Frozen sample and analysis

- Cities: the 51 cities in the frozen higher-vegetation-support GOES-19 holdout at longitude at or west of 100 degrees W.
- Intervals: the same ten outcome-independent 2025 intervals used in the GOES-19 holdout.
- Product: GOES-18 ABI Level-2 Land Surface Temperature, full-disk `ABI-L2-LSTC`.
- Spatial units, target hours, hydroclimatic severity, true-night heat definition, transition-shift outcome and quality rules are unchanged.
- Primary model: transition shift on severity per 10 percentile points among true-night heat observations, with city and interval fixed effects and exact interval-level Rademacher inference.

The identical western subset will also be estimated from the already extracted GOES-19 data. Agreement in sign across sensors supports an event-regime explanation; material disagreement indicates sensor/viewing sensitivity and precludes a sensor-general claim.
