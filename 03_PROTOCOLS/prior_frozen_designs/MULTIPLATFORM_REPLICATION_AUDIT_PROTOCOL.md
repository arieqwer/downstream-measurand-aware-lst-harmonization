# Multi-Platform Replication Audit Protocol

Frozen: 9 August 2026, before exact hourly pairing, viewing-geometry extraction,
or fitting the new harmonization models.

## Scientific question

How much do event selection, clear-sky observation availability, geostationary
platform/viewing geometry, and temporal transfer alter inference about the
urban-core minus surrounding-ring thermal transition across sunset?

The analysis is a measurement and replication study. It does not assume that
the transition is vegetation-specific or causally driven by soil moisture.

## Domains and platforms

1. Historical western overlap: GOES-16 and GOES-18, 2022-2024.
2. Frozen western holdout: GOES-18 and GOES-19, 2025.
3. Full historical GOES-16 census: 73 eligible intervals, with the 12
   originally selected intervals identified before this audit.

## Exact paired observations

Pair sensor observations by city, event interval, local date, target hour from
sunset, and QA definition. Retain only observations valid for both sensors and
require an absolute scan-time difference no greater than 15 minutes.

For each sensor, calculate:

- core LST;
- ring LST;
- core-minus-ring LST anomaly;
- pre-sunset anomaly (hours -3 to -1);
- late-post-sunset anomaly (hours +4 to +6); and
- late-minus-pre transition shift.

## Viewing geometry

Extract the nominal satellite subpoint and projection longitude from the
source-file metadata for each event/platform. Calculate city-level satellite
view zenith angle from the file-derived subpoint. Do not assign a constant
longitude from platform name alone.

## Prespecified tests

### Test 1: exact-pair sensor difference

Model the paired sensor difference in transition shift with city and event
fixed effects. The primary term is hydroclimatic severity per 10 points.
Inference uses intervals as the limiting clusters with Rademacher wild
bootstrap.

### Test 2: viewing-geometry moderation

Add severity multiplied by the centered difference in sensor view zenith
angle, plus scan-time difference and paired pre-sunset mean surface
temperature. Viewing geometry is considered explanatory only if the interaction
is supported and the residual platform-by-severity coefficient is attenuated
by at least 50% relative to Test 1.

### Test 3: platform-specific clear-sky availability

On the union of candidate city-events, model transition availability as a
function of severity, platform, and severity by platform. Use the same city and
event fixed effects and event-aware inference.

### Test 4: selected-event inflation

Within the complete 2018-2024 GOES-16 census, estimate the severity association
and its interaction with membership in the originally selected 12 intervals.
The selected-event interaction is the primary diagnostic. No new event
selection is permitted.

### Test 5: consensus and transfer

Estimate a cross-platform consensus severity slope using platform-specific
slopes and event-level inverse-variance random-effects synthesis. Report
heterogeneity. Evaluate transfer against the frozen 2025 estimates without
recalibration.

## Decision rules

A transferable physical signal requires positive cross-platform consensus,
transfer to the frozen 2025 evaluation, low cross-platform heterogeneity, and
support from a replicated physical mechanism. Measurement sensitivity alone is
insufficient. Physical interpretation additionally requires a stable
atmospheric or land-surface signal after harmonization and temporal transfer, or
a successful controlled physical-mechanism experiment.

## Claim guardrails

- Sensor differences are measurement/retrieval differences, not proof that one
  platform is correct.
- Event-selection effects do not prove misconduct or intentional cherry
  picking.
- Clear-sky availability effects identify selection risk, not the all-sky
  thermal state.
- A harmonized association remains observational and noncausal.
