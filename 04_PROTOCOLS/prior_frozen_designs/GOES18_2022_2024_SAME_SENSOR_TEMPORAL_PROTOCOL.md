# GOES-18 2022-2024 Same-Sensor Temporal Protocol

Frozen: 7 August 2026, before extraction or inspection of GOES-18 outcomes for
2022-2024.

## Purpose

GOES-16 estimates were positive in 2022-2024, whereas the frozen 2025 GOES-19
test was null to negative. This analysis separates temporal change from platform
change by applying the frozen analysis to GOES-18 in both periods.

## Population and intervals

- The 51 frozen higher-vegetation-support cities west of or at 100 degrees W
  used in the GOES-18 2025 replication.
- Every outcome-independent eligible interval in the 2022-2024 full census
  (31 intervals).
- GOES-18 ABI Level-2 LST (`ABI-L2-LSTC`).
- The existing urban core and 10-20 km surrounding-ring geometries.

## Frozen outcomes and inference

The strict `DQF = 0` transition shift is primary: late-post-sunset (+4 to +6 h)
minus pre-sunset (-3 to -1 h) core-minus-ring LST, with at least two valid days.
Hydroclimatic severity is scaled per 10 points. Models use city and interval
fixed effects and interval-level Rademacher wild-bootstrap inference.

The same-year sensor comparison pairs GOES-16 and GOES-18 city-event estimates
for 2022-2024. The same-sensor temporal comparison contrasts GOES-18 2022-2024
with GOES-18 2025. Neither city, interval, quality rule nor outcome will be
reselected after GOES-18 outcomes are opened.

## Decision rule

- A positive GOES-18 estimate in 2022-2024 followed by a null or negative 2025
  estimate supports temporal nonstationarity.
- A null GOES-18 estimate in 2022-2024 despite a positive paired GOES-16
  estimate supports platform or retrieval dependence.
- Inconsistent strict and recommended-QA results preclude a universal claim.
