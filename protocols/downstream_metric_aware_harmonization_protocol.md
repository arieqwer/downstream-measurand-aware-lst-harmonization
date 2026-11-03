# Downstream-metric-aware harmonization protocol

Frozen on 2026-08-10 before computing the exact MSE budgets or extracting any GOES-17 observations.

## Purpose

This analysis formalizes an already observed cross-platform measurement problem without changing, refitting or tuning any harmonization model against the opened 2026 holdout. It evaluates whether improvements in component measurements propagate to the downstream geospatial quantity used for inference.

## Measurement chain

For urban-core LST `C` and surrounding-ring LST `R`, the hourly spatial contrast is

`D = C - R`.

For pre-sunset and late-post-sunset windows, the transition metric is

`T = D_post - D_pre`.

The hierarchy is therefore component LST -> spatial contrast -> temporal transition.

## Exact downstream MSE budget

Let component errors relative to the reference platform be `e_c` and `e_r`, with means `b_c` and `b_r`. Using population moments within each fixed sample,

`MSE(D) = Var(e_c) + Var(e_r) - 2 Cov(e_c, e_r) + (b_c - b_r)^2`.

The downstream MSE gain from raw to component-harmonized observations is

`G_D = MSE_raw(D) - MSE_harm(D)`

and is decomposed exactly as

`G_D = G_variance + G_bias - P_covariance`,

where

`G_variance = [Var_c_raw - Var_c_harm] + [Var_r_raw - Var_r_harm]`,

`G_bias = (b_c_raw - b_r_raw)^2 - (b_c_harm - b_r_harm)^2`,

and

`P_covariance = 2 [Cov_raw(e_c,e_r) - Cov_harm(e_c,e_r)]`.

Positive `G_D` is improvement. Positive `P_covariance` is loss of beneficial covariance cancellation and therefore subtracts from the component variance and differential-bias gains. The same identity is applied to transition errors after deriving the core and ring transitions.

No theorem novelty is claimed. The methodological contribution is its use as an auditable acceptance criterion for a multisensor processing chain.

## Fixed empirical samples

The decomposition uses only existing predictions and no model refitting:

1. 2022-2024 expansion GOES-18/GOES-16;
2. 2025 original GOES-18/GOES-19;
3. 2025 expansion GOES-18/GOES-19; and
4. the prospectively fixed 2026 combined GOES-18/GOES-19 holdout.

All outputs, model choices and uncertainty widths remain exactly as produced by the earlier frozen protocols.

## Uncertainty

Point budgets are reported for all four samples. For the prospective 2026 holdout, 5,000 crossed city-event bootstrap draws quantify uncertainty in each budget term. Cities and events are resampled independently with replacement; their multiplicities are multiplied to form observation weights.

The algebraic closure residual must be less than `1e-10 K^2` for every point estimate and bootstrap draw, up to floating-point tolerance.

## Metric-aware decision framework

The scientific measurand determines whether a harmonization output is accepted.

1. `Component-wise correction`: use separately harmonized `C` and `R` only for component-level analyses when their out-of-sample loss improves.
2. `Direct downstream correction`: use a directly harmonized `D` or `T` only when the pre-holdout one-standard-error selector chooses it over raw observations.
3. `Raw retention`: retain the raw `D` or `T` when raw observations are selected by the frozen downstream model comparison.
4. `Directional abstention`: when the frozen uncertainty interval for `T` contains zero, do not certify its direction.

The 2026 holdout cannot select or alter any model, threshold or uncertainty width. It evaluates the decisions fixed from 2025 calibration.

## Claim boundary

The framework can demonstrate metric-dependent harmonizability, exact error propagation and selective downstream inference. It does not identify the physical source of angular discrepancies, create a universal satellite correction, or validate use beyond the tested platforms, domain and clear-sky conditions.

