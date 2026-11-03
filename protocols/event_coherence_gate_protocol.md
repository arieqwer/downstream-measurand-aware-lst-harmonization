# Multiscale Event-Coherence Gate Protocol

Frozen: 7 August 2026, after finding that the 2018-2024 coefficient disappears
inside the 2025 event-profile range and before fitting the interaction models
specified here.

## Question

Does city-level hydroclimatic severity alter the cross-sunset core-minus-ring
transition only when the wider North American event is spatially extensive?

## Outcome-independent coherence measure

The primary reference uses deterministic two-fold cross-fitting. The 184-city
higher-support cohort is divided by a SHA-256 hash of city ID; each city's event
context is calculated only from cities in the opposite fold. Compound-event
coverage is the fraction of that opposite fold simultaneously satisfying the
frozen city-specific true-night heat criterion and hydroclimatic severity of at
least 85.

A fully disjoint 113-city lower-vegetation-support network provides a second
reference definition. Both measures are computed from ERA5-Land and city
metadata without GOES LST or GOES availability.

The primary moderator is cross-fitted compound-event coverage per 10 percentage
points, centered at the 2018-2024 mean. Opposite-fold event-mean hydroclimatic
severity is a secondary continuous moderator, and disjoint-network coverage is
a reference-population sensitivity test. No outcome-selected coverage threshold
will be estimated.

## Model and temporal tests

Among strict-QA city-event observations satisfying true-night heat and at least
two valid transition days, transition shift is modeled with city and interval
fixed effects. Predictors are city-level severity, actual true-night 2-m air
temperature, pre-sunset mean core/ring LST and the severity-by-coherence
interaction. The coherence main effect is absorbed by interval fixed effects.

The positive interaction direction is tested separately in 2018-2021 and
2022-2024, then evaluated descriptively in the frozen 2025 holdout. Inference
uses an interval-level Rademacher wild bootstrap.

## Guardrail

Coherence is an event-scale effect modifier, not a teleconnection or causal
mechanism. It is eligible for a central claim only if the positive interaction
replicates in both historical temporal blocks, agrees under the cross-fitted and
disjoint reference definitions, and materially explains the weak 2025 marginal
estimate without an outcome-selected threshold.
