# GOES-19 2025 Lower-Vegetation External Validation Protocol

Frozen: 7 August 2026, before inspection of any 2025 GOES-19 temperature outcome.

## Purpose

This analysis tests whether the 2025 cross-sunset severity response is restricted to the higher-vegetation-support cohort. It uses every retained lower-vegetation-support city in the Northern American GOES-East domain and the exact intervals, outcomes, and quality rules frozen for the 2025 temporal and sensor holdout.

## Frozen population and intervals

- Cities: all 113 retained cities with `high_green = 0`, UN SDG region `Northern America`, longitude -125 to -66 degrees, latitude 24 to 50 degrees, and a valid 2025 hydroclimatic panel record.
- Satellite: GOES-19 ABI Level-2 LST (`ABI-L2-LSTC`).
- Intervals: the ten frozen 2025 intervals, steps 22-31. No interval is reselected using lower-vegetation GOES outcomes.
- Geometry: GHS urban-center core and 10-20 km surrounding ring.

## Frozen analysis

The primary lower-vegetation model is identical to the 2025 temporal and sensor holdout: transition shift on hydroclimatic severity per 10 points among true-night heat observations, with city and interval fixed effects and exact interval-level wild-bootstrap inference.

The cross-cohort test combines higher- and lower-vegetation cities and estimates `severity x higher-vegetation support` with city and interval fixed effects. A null interaction will be interpreted as evidence that the transition is a broader urban-surrounding hydroclimatic response rather than a uniquely vegetation-specific effect. A positive interaction will support stronger susceptibility in the higher-vegetation cohort. Neither outcome will be used to redefine the cohorts or intervals.
