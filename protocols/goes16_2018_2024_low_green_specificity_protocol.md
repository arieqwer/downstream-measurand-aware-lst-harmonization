# GOES-16 Historical Lower-Vegetation-Support Specificity Protocol

Frozen: 7 August 2026, before extraction or inspection of historical GOES-16
thermal outcomes for the lower-support cohort.

## Purpose

The primary historical hourly analysis was restricted to higher-vegetation-
support cities. This test applies the same event census, geometries, quality
rules, transition outcome, and hydroclimatic exposure to a disjoint lower-
support cohort.

## Frozen sample and outcome

- 113 lower-vegetation-support North American cities selected before GOES
  outcome extraction.
- All 73 outcome-independent eligible intervals from 2018-2024.
- GOES-16 ABI Level-2 LST (`ABI-L2-LSTC`).
- Existing urban-core and 10-20 km surrounding-ring geometries.
- Strict `DQF = 0` transition shift from hours -3 to -1 to hours +4 to +6,
  requiring at least two valid days.

## Frozen inference and decision rule

City and interval fixed effects estimate the transition-shift association per
10 hydroclimatic-severity points, with interval-level Rademacher wild-bootstrap
inference. The primary pooled higher-versus-lower-support model adjusts for
true-night 2-m air temperature and pre-sunset mean surface temperature and
tests the severity-by-support interaction; an unadjusted model is secondary. A
second baseline-adjusted diagnostic models the late-post-sunset core-ring
anomaly while controlling the pre-sunset core-ring anomaly and the same thermal
covariates.
Vegetation specificity is supported only if that
interaction is positive and event-aware inference excludes zero. Similar
associations in both cohorts, or a null interaction, require an urban-surface
rather than vegetation-specific interpretation.
