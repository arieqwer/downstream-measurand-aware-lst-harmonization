# Multiplatform Replication Audit: Protocol Amendment 01

Frozen: 10 August 2026, before inspection of hour-resolved cross-platform
component differences.

## Rationale

The prespecified exact-pair audit identified a systematic difference in the
pre-to-post-sunset core-minus-ring transition between paired GOES platforms.
The aggregate result does not show whether that offset is concentrated at a
particular hour or whether it originates mainly in core or surrounding-ring
retrievals. This amendment decomposes that already-detected measurement offset;
it does not redefine the hydroclimatic outcome or add a new mechanism claim.

## Frozen diagnostics

For each prespecified platform pair, retain only exact city-date-hour matches
with recommended quality on both platforms, scan separation no greater than
15 minutes, and true-night heat as defined in the parent protocol.

1. Estimate event-equal mean platform differences in core LST, ring LST, and
   core-minus-ring anomaly for every integer hour from -3 to +6 relative to
   sunset. Use an event-block bootstrap for 95% confidence intervals.
2. Decompose the platform difference in the pre-to-late transition into the
   difference in core cooling and the difference in ring cooling, using the
   same pre (-3 to -1 hours), late (+4 to +6 hours), minimum-hour, and
   minimum-day rules as the parent audit.
3. As an explicitly exploratory diagnostic, regress the city-event transition
   difference on the difference in nominal view zenith angle with event fixed
   effects and city-clustered uncertainty. This association will not be
   interpreted causally because viewing geometry is spatially confounded.

## Interpretation guardrail

A systematic hour-dependent offset establishes a platform-transfer limitation
for absolute transition metrics. It does not by itself invalidate a
hydroclimatic slope if the exact-common-support sensor-by-severity interaction
is unsupported. Conversely, a null view-angle association does not establish
platform equivalence because radiometric, atmospheric, parallax, emissivity,
and mixed-pixel differences remain unresolved.
