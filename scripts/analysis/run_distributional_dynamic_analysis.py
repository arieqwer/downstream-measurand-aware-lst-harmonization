from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from scipy.stats import ttest_1samp

from analysis_utils import bootstrap_mean_ci, holm_adjust, twfe_cluster_ols


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/external/valid_city_interval_panel.parquet"
CITY = ROOT / "data/processed/city_covariates.csv"
OUT = ROOT / "data/processed/analysis_outputs"
RANDOM_SEED = 20260714

MATCH_COVARIATES = [
    "log_population",
    "median_true_night_t2m_c",
    "median_true_night_wetbulb_c",
    "mean_vpd_kpa",
    "mean_rzsm",
    "mean_log1p_pr_sum",
    "mean_gradient_mld",
    "valid_core_ring_fraction",
]


def standardized(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        standard_deviation = result[column].std(ddof=0)
        result[f"z_{column}"] = (result[column] - result[column].mean()) / standard_deviation
    return result


def optimal_exact_matching(city: pd.DataFrame) -> pd.DataFrame:
    work = city.dropna(subset=["un_sdg_reg", "wb_income", *MATCH_COVARIATES]).copy()
    work["population_quintile"] = pd.qcut(
        work["log_population"], q=5, labels=False, duplicates="drop"
    )
    work["night_temperature_tercile"] = pd.qcut(
        work["median_true_night_t2m_c"], q=3, labels=False, duplicates="drop"
    )
    work["soil_moisture_tercile"] = pd.qcut(
        work["mean_rzsm"], q=3, labels=False, duplicates="drop"
    )
    work = standardized(work, MATCH_COVARIATES)
    z_columns = [f"z_{column}" for column in MATCH_COVARIATES]
    rows: list[dict] = []

    exact_columns = [
        "un_sdg_reg",
        "wb_income",
        "population_quintile",
        "night_temperature_tercile",
        "soil_moisture_tercile",
    ]
    for exact_values, stratum in work.groupby(exact_columns, sort=True):
        region, income, population_quintile, night_temperature_tercile, soil_moisture_tercile = exact_values
        high = stratum[stratum["high_green"].eq(1)].reset_index(drop=True)
        low = stratum[stratum["high_green"].eq(0)].reset_index(drop=True)
        if high.empty or low.empty:
            continue
        distance = cdist(high[z_columns].to_numpy(), low[z_columns].to_numpy(), metric="euclidean")
        high_index, low_index = linear_sum_assignment(distance)
        for high_row, low_row in zip(high_index, low_index):
            rows.append(
                {
                    "high_uc_id": high.loc[high_row, "uc_id"],
                    "low_uc_id": low.loc[low_row, "uc_id"],
                    "un_sdg_reg": region,
                    "wb_income": income,
                    "population_quintile": int(population_quintile),
                    "night_temperature_tercile": int(night_temperature_tercile),
                    "soil_moisture_tercile": int(soil_moisture_tercile),
                    "match_distance": float(distance[high_row, low_row]),
                }
            )
    return pd.DataFrame(rows)


def matching_balance(city: pd.DataFrame, pairs: pd.DataFrame) -> pd.DataFrame:
    high = city[city["high_green"].eq(1)].set_index("uc_id")
    low = city[city["high_green"].eq(0)].set_index("uc_id")
    rows = []
    for column in MATCH_COVARIATES:
        before_pooled = np.sqrt((high[column].var(ddof=1) + low[column].var(ddof=1)) / 2)
        before = (high[column].mean() - low[column].mean()) / before_pooled
        matched_high = high.loc[pairs["high_uc_id"], column].to_numpy()
        matched_low = low.loc[pairs["low_uc_id"], column].to_numpy()
        after_pooled = np.sqrt((matched_high.var(ddof=1) + matched_low.var(ddof=1)) / 2)
        after = (matched_high.mean() - matched_low.mean()) / after_pooled
        rows.append(
            {
                "covariate": column,
                "standardized_difference_before": before,
                "standardized_difference_after": after,
                "absolute_standardized_difference_after": abs(after),
            }
        )
    return pd.DataFrame(rows)


def city_distributional_shifts(
    panel: pd.DataFrame, minimum_intervals: int, quantiles: list[float]
) -> pd.DataFrame:
    records = []
    for uc_id, city in panel.groupby("uc_id", sort=False):
        mld = city.loc[city["mld"].eq(1), "core_minus_ring_tb_night_anom"]
        dhd = city.loc[city["dhd"].eq(1), "core_minus_ring_tb_night_anom"]
        extreme = city.loc[city["extreme_dhd"].eq(1), "core_minus_ring_tb_night_anom"]
        if len(mld) < minimum_intervals or len(dhd) < minimum_intervals:
            continue
        record = {
            "uc_id": uc_id,
            "n_mld": len(mld),
            "n_dhd": len(dhd),
            "n_extreme_dhd": len(extreme),
        }
        for quantile in quantiles:
            label = int(100 * quantile)
            mld_value = mld.quantile(quantile)
            record[f"dhd_minus_mld_q{label}"] = dhd.quantile(quantile) - mld_value
            record[f"extreme_dhd_minus_mld_q{label}"] = (
                extreme.quantile(quantile) - mld_value
                if len(extreme) >= minimum_intervals
                else np.nan
            )
        records.append(record)
    return pd.DataFrame(records)


def matched_distributional_results(
    shifts: pd.DataFrame,
    pairs: pd.DataFrame,
    minimum_intervals: int,
    quantiles: list[float],
    random: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    high = shifts.add_prefix("high_")
    low = shifts.add_prefix("low_")
    merged = (
        pairs.merge(high, left_on="high_uc_id", right_on="high_uc_id", how="inner")
        .merge(low, left_on="low_uc_id", right_on="low_uc_id", how="inner")
    )
    rows = []
    pair_rows = []
    for contrast in ["dhd_minus_mld", "extreme_dhd_minus_mld"]:
        for quantile in quantiles:
            label = int(100 * quantile)
            column = f"{contrast}_q{label}"
            pair_effect = merged[f"high_{column}"] - merged[f"low_{column}"]
            pair_effect = pair_effect.dropna()
            ci_low, ci_high = bootstrap_mean_ci(pair_effect.to_numpy(), random)
            test = ttest_1samp(pair_effect, popmean=0, nan_policy="omit")
            rows.append(
                {
                    "minimum_intervals_per_state": minimum_intervals,
                    "contrast": contrast,
                    "quantile": quantile,
                    "n_pairs": len(pair_effect),
                    "matched_high_minus_low_shift": pair_effect.mean(),
                    "std_error": pair_effect.std(ddof=1) / np.sqrt(len(pair_effect)),
                    "bootstrap_ci95_low": ci_low,
                    "bootstrap_ci95_high": ci_high,
                    "p_value": test.pvalue,
                }
            )
            for pair_index, value in pair_effect.items():
                pair_rows.append(
                    {
                        "minimum_intervals_per_state": minimum_intervals,
                        "contrast": contrast,
                        "quantile": quantile,
                        "pair_index": pair_index,
                        "pair_effect": value,
                    }
                )
    results = pd.DataFrame(rows)
    results["p_value_holm_within_contrast"] = results.groupby("contrast")["p_value"].transform(
        holm_adjust
    )
    return results, pd.DataFrame(pair_rows)


def add_consecutive_lags(panel: pd.DataFrame) -> pd.DataFrame:
    work = panel.sort_values(["uc_id", "time_id"]).copy()
    grouped = work.groupby("uc_id", sort=False)
    lag_time = grouped["time_id"].shift()
    consecutive = work["time_id"].sub(lag_time).eq(1)
    for column in [
        "core_minus_ring_tb_night_anom",
        "dhd",
        "mld",
        "extreme_dhd",
        "heat_true_night_t2m_local_p90",
    ]:
        work[f"lag1_{column}"] = grouped[column].shift().where(consecutive)
    return work[work["lag1_core_minus_ring_tb_night_anom"].notna()].copy()


def transition_profiles(panel: pd.DataFrame, thresholds: list[float]) -> pd.DataFrame:
    rows = []
    masks = {
        "mld": panel["mld"].eq(1),
        "dhd": panel["dhd"].eq(1),
        "extreme_dhd": panel["extreme_dhd"].eq(1),
        "dhd_true_night_heat": panel["dhd"].eq(1)
        & panel["heat_true_night_t2m_local_p90"].eq(1),
        "extreme_dhd_true_night_heat": panel["extreme_dhd"].eq(1)
        & panel["heat_true_night_t2m_local_p90"].eq(1),
    }
    for threshold in thresholds:
        current = panel["core_minus_ring_tb_night_anom"].gt(threshold)
        previous = panel["lag1_core_minus_ring_tb_night_anom"].gt(threshold)
        for state, state_mask in masks.items():
            for group in ["high_veg", "low_veg"]:
                group_mask = panel["veg_group"].eq(group)
                onset_mask = state_mask & group_mask & ~previous
                persistence_mask = state_mask & group_mask & previous
                onset = current[onset_mask].mean()
                persistence = current[persistence_mask].mean()
                rows.append(
                    {
                        "anomaly_threshold_c": threshold,
                        "hydroclimatic_state": state,
                        "veg_group": group,
                        "n_onset_eligible": int(onset_mask.sum()),
                        "onset_probability": onset,
                        "n_persistence_eligible": int(persistence_mask.sum()),
                        "persistence_probability": persistence,
                        "recovery_probability": 1 - persistence,
                        "onset_to_recovery_ratio": onset / (1 - persistence),
                    }
                )
    return pd.DataFrame(rows)


def city_transition_shifts(panel: pd.DataFrame, threshold: float, minimum_eligible: int = 10) -> pd.DataFrame:
    work = panel.copy()
    work["current_loss"] = work["core_minus_ring_tb_night_anom"].gt(threshold).astype("int8")
    work["previous_loss"] = work["lag1_core_minus_ring_tb_night_anom"].gt(threshold).astype("int8")
    records = []
    for uc_id, city in work.groupby("uc_id", sort=False):
        record = {"uc_id": uc_id}
        complete = True
        for state, state_mask in {
            "mld": city["mld"].eq(1),
            "dhd": city["dhd"].eq(1),
        }.items():
            onset = city[state_mask & city["previous_loss"].eq(0)]
            persistence = city[state_mask & city["previous_loss"].eq(1)]
            if len(onset) < minimum_eligible or len(persistence) < minimum_eligible:
                complete = False
                break
            record[f"onset_{state}"] = onset["current_loss"].mean()
            record[f"persistence_{state}"] = persistence["current_loss"].mean()
        if complete:
            record["onset_shift_dhd_minus_mld"] = record["onset_dhd"] - record["onset_mld"]
            record["persistence_shift_dhd_minus_mld"] = (
                record["persistence_dhd"] - record["persistence_mld"]
            )
            records.append(record)
    return pd.DataFrame(records)


def matched_transition_results(
    city_shifts: pd.DataFrame,
    pairs: pd.DataFrame,
    threshold: float,
    random: np.random.Generator,
) -> pd.DataFrame:
    high = city_shifts.add_prefix("high_")
    low = city_shifts.add_prefix("low_")
    merged = (
        pairs.merge(high, left_on="high_uc_id", right_on="high_uc_id", how="inner")
        .merge(low, left_on="low_uc_id", right_on="low_uc_id", how="inner")
    )
    rows = []
    for outcome in ["onset_shift_dhd_minus_mld", "persistence_shift_dhd_minus_mld"]:
        effect = (merged[f"high_{outcome}"] - merged[f"low_{outcome}"]).dropna()
        ci_low, ci_high = bootstrap_mean_ci(effect.to_numpy(), random)
        test = ttest_1samp(effect, popmean=0)
        rows.append(
            {
                "anomaly_threshold_c": threshold,
                "outcome": outcome,
                "n_pairs": len(effect),
                "matched_high_minus_low_dhd_mld_shift": effect.mean(),
                "std_error": effect.std(ddof=1) / np.sqrt(len(effect)),
                "bootstrap_ci95_low": ci_low,
                "bootstrap_ci95_high": ci_high,
                "p_value": test.pvalue,
            }
        )
    return pd.DataFrame(rows)


def transition_twfe(panel: pd.DataFrame, thresholds: list[float]) -> pd.DataFrame:
    model_rows = []
    state_sample = panel[panel["dhd"].eq(1) | panel["mld"].eq(1)].copy()
    state_sample["hot"] = state_sample["heat_true_night_t2m_local_p90"].astype(float)
    state_sample["stress"] = state_sample["dhd"].astype(float)
    state_sample["stress_high"] = state_sample["stress"] * state_sample["high_green"]
    state_sample["hot_high"] = state_sample["hot"] * state_sample["high_green"]
    state_sample["stress_zgreen"] = (
        state_sample["stress"] * state_sample["z_ring_green_support"]
    )
    state_sample["hot_zgreen"] = state_sample["hot"] * state_sample["z_ring_green_support"]
    state_sample["lag1_stress"] = state_sample["lag1_dhd"].fillna(0).astype(float)
    state_sample["lag1_hot"] = (
        state_sample["lag1_heat_true_night_t2m_local_p90"].fillna(0).astype(float)
    )

    binary_predictors = [
        "stress",
        "hot",
        "stress_high",
        "hot_high",
        "lag1_core_minus_ring_tb_night_anom",
        "lag1_stress",
        "lag1_hot",
    ]
    continuous_predictors = [
        "stress",
        "hot",
        "stress_zgreen",
        "hot_zgreen",
        "lag1_core_minus_ring_tb_night_anom",
        "lag1_stress",
        "lag1_hot",
    ]

    for threshold in thresholds:
        current = state_sample["core_minus_ring_tb_night_anom"].gt(threshold).astype(float)
        previous = state_sample["lag1_core_minus_ring_tb_night_anom"].gt(threshold)
        state_sample["transition_outcome"] = current
        for transition, eligibility in {"onset": ~previous, "persistence": previous}.items():
            subset = state_sample[eligibility].copy()
            model_rows.append(
                twfe_cluster_ols(
                    subset,
                    outcome="transition_outcome",
                    predictors=binary_predictors,
                    model_name=f"{transition}_binary_high_threshold_{threshold:g}",
                )
            )
            if threshold == 0:
                model_rows.append(
                    twfe_cluster_ols(
                        subset,
                        outcome="transition_outcome",
                        predictors=continuous_predictors,
                        model_name=f"{transition}_continuous_green_threshold_0",
                    )
                )
    return pd.concat(model_rows, ignore_index=True)


def corrected_headline_summary(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    masks = {
        "mld": panel["mld"].eq(1),
        "dhd": panel["dhd"].eq(1),
        "extreme_dhd": panel["extreme_dhd"].eq(1),
    }
    for state, state_mask in masks.items():
        for group in ["high_veg", "low_veg"]:
            subset = panel[state_mask & panel["veg_group"].eq(group)]
            event = subset["heat_true_night_t2m_local_p90"].eq(1) & subset["loss_state"].eq(1)
            hot = subset[subset["heat_true_night_t2m_local_p90"].eq(1)]
            rows.append(
                {
                    "hydroclimatic_state": state,
                    "veg_group": group,
                    "n_valid_intervals": len(subset),
                    "n_cities": subset["uc_id"].nunique(),
                    "mean_core_ring_anomaly_c": subset["core_minus_ring_tb_night_anom"].mean(),
                    "positive_anomaly_probability": subset["loss_state"].mean(),
                    "true_night_heat_probability": subset["heat_true_night_t2m_local_p90"].mean(),
                    "compound_loss_probability_among_valid_state_intervals": event.mean(),
                    "positive_anomaly_probability_given_true_night_heat": hot["loss_state"].mean(),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    random = np.random.default_rng(RANDOM_SEED)
    panel_columns = [
        "uc_id",
        "veg_group",
        "year",
        "step8",
        "time_id",
        "dhd",
        "mld",
        "extreme_dhd",
        "heat_true_night_t2m_local_p90",
        "core_minus_ring_tb_night_anom",
        "loss_state",
        "high_green",
        "z_ring_green_support",
        "population_2025",
    ]
    panel = pd.read_parquet(PANEL, columns=panel_columns)
    panel["uc_id"] = panel["uc_id"].astype(str)
    city = pd.read_csv(CITY, dtype={"uc_id": str})

    pairs = optimal_exact_matching(city)
    pairs.to_csv(OUT / "optimal_exact_matched_pairs.csv", index=False)
    matching_balance(city, pairs).to_csv(OUT / "optimal_matching_balance.csv", index=False)

    quantiles = [0.50, 0.75, 0.90, 0.95]
    distributional_results = []
    distributional_pair_results = []
    for minimum in [5, 10, 20]:
        shifts = city_distributional_shifts(panel, minimum, quantiles)
        results, pair_results = matched_distributional_results(
            shifts, pairs, minimum, quantiles, random
        )
        distributional_results.append(results)
        distributional_pair_results.append(pair_results)
    pd.concat(distributional_results, ignore_index=True).to_csv(
        OUT / "matched_distributional_quantile_results.csv", index=False
    )
    pd.concat(distributional_pair_results, ignore_index=True).to_csv(
        OUT / "matched_distributional_pair_effects.csv", index=False
    )

    transitions = add_consecutive_lags(panel)
    thresholds = [0.0, 0.10, 0.25, 0.50]
    transition_profiles(transitions, thresholds).to_csv(
        OUT / "transition_profiles.csv", index=False
    )
    matched_transition = []
    for threshold in thresholds:
        city_shifts = city_transition_shifts(transitions, threshold)
        matched_transition.append(matched_transition_results(city_shifts, pairs, threshold, random))
    pd.concat(matched_transition, ignore_index=True).to_csv(
        OUT / "matched_transition_results.csv", index=False
    )

    transition_twfe(transitions, thresholds).to_csv(
        OUT / "transition_twfe_model_terms.csv", index=False
    )
    corrected_headline_summary(panel).to_csv(OUT / "corrected_headline_summary.csv", index=False)

    print(f"Optimal no-replacement pairs: {len(pairs):,}")
    print("\nMatching balance")
    print(pd.read_csv(OUT / "optimal_matching_balance.csv").round(4).to_string(index=False))
    print("\nPrimary distributional results")
    primary = pd.read_csv(OUT / "matched_distributional_quantile_results.csv")
    print(primary[primary["minimum_intervals_per_state"].eq(10)].round(5).to_string(index=False))
    print("\nMatched transition results")
    print(pd.read_csv(OUT / "matched_transition_results.csv").round(5).to_string(index=False))
    print("\nKey TWFE terms")
    terms = pd.read_csv(OUT / "transition_twfe_model_terms.csv")
    print(
        terms[terms["term"].isin(["stress_high", "stress_zgreen"])]
        .round(6)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
