# GOES sunset mechanism protocol

Frozen: 6 August 2026, before the complete extraction or outcome models were opened.

## Scientific test

The analysis tests whether compound hydroclimatic severity is associated with a
change in the sunset-aligned urban-core minus 10-20 km ring LST trajectory, and
whether independently measured built intensity selectively modifies that change
after sunset.

## Sample

- Sixty high-green-support cities in the GOES-16 CONUS domain.
- Twelve independently selected 8-day intervals from 2018-2024.
- Interval selection used hydroclimatic severity and true-night air-temperature
  rank, but no GOES thermal outcome.
- Hourly observations span three hours before through six hours after local
  astronomical sunset.

## Quality and estimands

- Primary quality screen: DQF = 0 (strict).
- Sensitivity screen: DQF <= 1 (conditionally usable observations included).
- A city-day slope requires at least four post-sunset hours spanning at least
  three hours. A city-event estimate requires at least two valid days.
- Co-primary outcomes: post-sunset core-minus-ring LST slope and the change from
  the pre-sunset mean anomaly to the late post-sunset mean anomaly.
- Supporting outcome: late post-sunset core-minus-ring anomaly.
- Negative-time control: the core-minus-ring slope during hours -3 to -1.

## Models and validation

- City and interval fixed effects with city-clustered uncertainty.
- Predictors: continuous hydroclimatic severity, severity by water support,
  severity by built intensity, and true-night heat rank.
- Severe-hot versus lower-severity-hot within-city state contrast.
- Temporal validation: 2018-2021 discovery and 2022-2024 confirmation periods.

## Decision rule

The direct carryover mechanism is supported only if the strict-quality results
show a post-sunset hydroclimatic or built-modified trajectory change, the
negative-time control is absent or materially weaker, and the key direction is
consistent in both temporal periods. Mixed evidence will be reported as partial
validation; null or contradictory evidence will falsify the proposed direct
hourly mechanism.

