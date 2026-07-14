from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_1samp

from analysis_utils import bootstrap_mean_ci, twfe_cluster_ols
from run_diurnal_inversion_mechanism import build_storage_score
from run_diurnal_inversion_mechanism import BUILT_FORM, BUILT_FORM_FEATURES


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/external/valid_city_interval_panel.parquet"
PAIRS = ROOT / "data/processed/analysis_outputs/optimal_exact_matched_pairs.csv"
OUT = ROOT / "data/processed/analysis_outputs"
RANDOM_SEED = 20260714
OVERPASS_SEPARATION_HOURS = 12.0
STATES = ["mld", "dhd", "extreme_dhd"]


def prepare() -> pd.DataFrame:
    columns = [
        "uc_id",
        "year",
        "time_id",
        "analysis_state",
        "high_green",
        "z_ring_green_support",
        "un_sdg_reg",
        "heat_true_night_t2m_local_p90",
        "t2m_true_night_pct_rank",
        "vpd_pct",
        "rzsm_pct",
        "core_tb_day",
        "ring_tb_day",
        "core_tb_night",
        "ring_tb_night",
        "core_n_built_day",
        "ring_n_built_day",
        "core_n_built_night",
        "ring_n_built_night",
    ]
    frame = pd.read_parquet(PANEL, columns=columns)
    for unit in ["core", "ring"]:
        frame[f"{unit}_decay_h"] = np.log(
            (frame[f"{unit}_tb_day"] + 273.15) / (frame[f"{unit}_tb_night"] + 273.15)
        ) / OVERPASS_SEPARATION_HOURS
    # Scaling by 10^4 keeps coefficients readable; the underlying unit is h^-1.
    frame["differential_decay_1e4_h"] = (
        frame["core_decay_h"] - frame["ring_decay_h"]
    ) * 1e4
    frame["is_dhd"] = frame["analysis_state"].eq("dhd").astype(float)
    frame["is_extreme_dhd"] = frame["analysis_state"].eq("extreme_dhd").astype(float)
    for column in ["t2m_true_night_pct_rank", "vpd_pct", "rzsm_pct"]:
        frame[f"z_{column}"] = (frame[column] - frame[column].mean()) / frame[column].std(ddof=0)
    return frame


def state_summary(frame: pd.DataFrame, sample: str) -> pd.DataFrame:
    paired = frame.dropna(subset=["core_decay_h", "ring_decay_h", "differential_decay_1e4_h"])
    interval_weighted = (
        paired[paired["analysis_state"].isin(STATES)]
        .groupby(["high_green", "analysis_state"], as_index=False)
        .agg(
            n_paired_intervals=("time_id", "size"),
            n_cities=("uc_id", "nunique"),
            mean_core_decay_1e4_h=("core_decay_h", lambda x: x.mean() * 1e4),
            mean_ring_decay_1e4_h=("ring_decay_h", lambda x: x.mean() * 1e4),
            mean_differential_decay_1e4_h=("differential_decay_1e4_h", "mean"),
        )
        .assign(sample=sample, weighting="interval")
    )
    city_state = (
        paired[paired["analysis_state"].isin(STATES)]
        .groupby(["uc_id", "high_green", "analysis_state"], as_index=False)
        .agg(
            mean_core_decay_1e4_h=("core_decay_h", lambda x: x.mean() * 1e4),
            mean_ring_decay_1e4_h=("ring_decay_h", lambda x: x.mean() * 1e4),
            mean_differential_decay_1e4_h=("differential_decay_1e4_h", "mean"),
            n_paired_intervals=("time_id", "size"),
        )
    )
    city_weighted = (
        city_state.groupby(["high_green", "analysis_state"], as_index=False)
        .agg(
            n_paired_intervals=("n_paired_intervals", "sum"),
            n_cities=("uc_id", "size"),
            mean_core_decay_1e4_h=("mean_core_decay_1e4_h", "mean"),
            mean_ring_decay_1e4_h=("mean_ring_decay_1e4_h", "mean"),
            mean_differential_decay_1e4_h=("mean_differential_decay_1e4_h", "mean"),
            se_differential_decay_1e4_h=(
                "mean_differential_decay_1e4_h",
                lambda x: x.std(ddof=1) / np.sqrt(len(x)),
            ),
        )
        .assign(sample=sample, weighting="city")
    )
    return pd.concat([interval_weighted, city_weighted], ignore_index=True, sort=False)


def matched_contrasts(
    frame: pd.DataFrame, pairs: pd.DataFrame, random: np.random.Generator
) -> pd.DataFrame:
    city_state = (
        frame[frame["analysis_state"].isin(STATES)]
        .groupby(["uc_id", "analysis_state"], as_index=False)
        .agg(
            n_intervals=("time_id", "size"),
            differential_decay_1e4_h=("differential_decay_1e4_h", "mean"),
        )
    )
    wide = city_state.pivot(index="uc_id", columns="analysis_state")
    rows = []
    for state in ["dhd", "extreme_dhd"]:
        shifts = pd.DataFrame(
            {
                "uc_id": wide.index,
                "shift": wide[("differential_decay_1e4_h", state)]
                - wide[("differential_decay_1e4_h", "mld")],
                "n_mld": wide[("n_intervals", "mld")],
                "n_stress": wide[("n_intervals", state)],
            }
        ).dropna()
        shifts = shifts[(shifts["n_mld"] >= 10) & (shifts["n_stress"] >= 10)].set_index(
            "uc_id"
        )
        matched = (
            pairs.merge(shifts[["shift"]], left_on="high_uc_id", right_index=True)
            .rename(columns={"shift": "high_shift"})
            .merge(shifts[["shift"]], left_on="low_uc_id", right_index=True)
            .rename(columns={"shift": "low_shift"})
        )
        effect = (matched["high_shift"] - matched["low_shift"]).to_numpy(dtype=float)
        ci_low, ci_high = bootstrap_mean_ci(effect, random)
        test = ttest_1samp(effect, popmean=0.0)
        rows.append(
            {
                "contrast": f"{state}_minus_mld",
                "n_pairs": len(effect),
                "matched_high_minus_low_differential_decay_shift_1e4_h": effect.mean(),
                "std_error": effect.std(ddof=1) / np.sqrt(len(effect)),
                "bootstrap_ci95_low": ci_low,
                "bootstrap_ci95_high": ci_high,
                "p_value": test.pvalue,
            }
        )
    return pd.DataFrame(rows)


def add_storage(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    merged = frame.merge(city, on="uc_id", how="left", validate="many_to_one")
    for feature in [
        "built_form_storage_score",
        "z_ventilation_obstruction_index",
        "z_ahe_night_wm2",
    ]:
        merged[f"dhd_x_{feature}"] = merged["is_dhd"] * merged[feature]
        merged[f"extreme_x_{feature}"] = merged["is_extreme_dhd"] * merged[feature]
    return merged


def models(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    states = frame[frame["analysis_state"].isin(STATES)].copy()
    states["dhd_x_high_green"] = states["is_dhd"] * states["high_green"]
    states["extreme_x_high_green"] = states["is_extreme_dhd"] * states["high_green"]
    states["dhd_x_green_support"] = states["is_dhd"] * states["z_ring_green_support"]
    states["extreme_x_green_support"] = (
        states["is_extreme_dhd"] * states["z_ring_green_support"]
    )
    controls = [
        "is_dhd",
        "is_extreme_dhd",
        "z_t2m_true_night_pct_rank",
        "z_vpd_pct",
        "z_rzsm_pct",
    ]
    rows = [
        twfe_cluster_ols(
            states,
            "differential_decay_1e4_h",
            [*controls, "dhd_x_high_green", "extreme_x_high_green"],
            model_name="differential_decay_high_green",
        ),
        twfe_cluster_ols(
            states,
            "differential_decay_1e4_h",
            [*controls, "dhd_x_green_support", "extreme_x_green_support"],
            model_name="differential_decay_continuous_green_support",
        ),
    ]
    high = add_storage(states[states["high_green"].eq(1)].copy(), city)
    for feature in [
        "built_form_storage_score",
        "z_ventilation_obstruction_index",
        "z_ahe_night_wm2",
    ]:
        rows.append(
            twfe_cluster_ols(
                high,
                "differential_decay_1e4_h",
                [*controls, f"dhd_x_{feature}", f"extreme_x_{feature}"],
                model_name=f"differential_decay_{feature}",
            )
        )
    return pd.concat(rows, ignore_index=True)


def sampling_sensitivity(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    high = add_storage(
        frame[frame["high_green"].eq(1) & frame["analysis_state"].isin(STATES)].copy(), city
    )
    support = [
        "core_n_built_day",
        "ring_n_built_day",
        "core_n_built_night",
        "ring_n_built_night",
    ]
    rows = []
    for minimum in [5, 10, 20]:
        subset = high[high[support].ge(minimum).all(axis=1)]
        model = twfe_cluster_ols(
            subset,
            "differential_decay_1e4_h",
            [
                "is_dhd",
                "is_extreme_dhd",
                "z_t2m_true_night_pct_rank",
                "z_vpd_pct",
                "z_rzsm_pct",
                "dhd_x_built_form_storage_score",
                "extreme_x_built_form_storage_score",
            ],
            model_name=f"minimum_{minimum}_built_pixels",
        )
        rows.append(model[model["term"].str.contains("built_form_storage_score")])
    for unit in ["core", "ring"]:
        denominator = high[[f"{unit}_n_built_day", f"{unit}_n_built_night"]].max(axis=1)
        high[f"{unit}_day_night_count_imbalance"] = (
            high[f"{unit}_n_built_day"] - high[f"{unit}_n_built_night"]
        ).abs() / denominator
    high["maximum_day_night_count_imbalance"] = high[
        ["core_day_night_count_imbalance", "ring_day_night_count_imbalance"]
    ].max(axis=1)
    for maximum in [0.25, 0.10, 0.05]:
        subset = high[high["maximum_day_night_count_imbalance"] <= maximum]
        model = twfe_cluster_ols(
            subset,
            "differential_decay_1e4_h",
            [
                "is_dhd",
                "is_extreme_dhd",
                "z_t2m_true_night_pct_rank",
                "z_vpd_pct",
                "z_rzsm_pct",
                "dhd_x_built_form_storage_score",
                "extreme_x_built_form_storage_score",
            ],
            model_name=f"maximum_{maximum:.2f}_day_night_count_imbalance",
        )
        rows.append(model[model["term"].str.contains("built_form_storage_score")])
    return pd.concat(rows, ignore_index=True)


def storage_quartile_summary(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    high = frame[
        frame["high_green"].eq(1) & frame["analysis_state"].isin(STATES)
    ].merge(city, on="uc_id", how="left", validate="many_to_one")
    city_score = city.dropna(subset=["built_form_storage_score"]).copy()
    city_score["storage_quartile"] = pd.qcut(
        city_score["built_form_storage_score"],
        4,
        labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"],
    )
    high = high.merge(
        city_score[["uc_id", "storage_quartile"]],
        on="uc_id",
        how="inner",
        validate="many_to_one",
    )
    city_state = (
        high.groupby(["uc_id", "storage_quartile", "analysis_state"], observed=True)
        .agg(
            differential_decay_1e4_h=("differential_decay_1e4_h", "mean"),
            n_intervals=("time_id", "size"),
        )
        .reset_index()
    )
    wide = city_state.pivot(index=["uc_id", "storage_quartile"], columns="analysis_state")
    rows = []
    for state in ["dhd", "extreme_dhd"]:
        shifts = (
            wide[("differential_decay_1e4_h", state)]
            - wide[("differential_decay_1e4_h", "mld")]
        ).rename("stress_minus_mld_shift").reset_index()
        support = (
            (wide[("n_intervals", state)] >= 10)
            & (wide[("n_intervals", "mld")] >= 10)
        ).rename("supported").reset_index(drop=True)
        shifts["supported"] = support
        shifts = shifts[shifts["supported"]]
        for quartile, subset in shifts.groupby("storage_quartile", observed=True):
            values = subset["stress_minus_mld_shift"].to_numpy(dtype=float)
            rows.append(
                {
                    "contrast": f"{state}_minus_mld",
                    "storage_quartile": str(quartile),
                    "n_cities": len(values),
                    "mean_differential_decay_shift_1e4_h": values.mean(),
                    "standard_error": values.std(ddof=1) / np.sqrt(len(values)),
                }
            )
    return pd.DataFrame(rows)


def subgroup_storage_models(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    high = add_storage(
        frame[frame["high_green"].eq(1) & frame["analysis_state"].isin(STATES)].copy(),
        city,
    )
    controls = [
        "is_dhd",
        "is_extreme_dhd",
        "z_t2m_true_night_pct_rank",
        "z_vpd_pct",
        "z_rzsm_pct",
        "dhd_x_built_form_storage_score",
        "extreme_x_built_form_storage_score",
    ]
    rows = []
    for region, subset in high.groupby("un_sdg_reg", sort=True):
        model = twfe_cluster_ols(
            subset,
            "differential_decay_1e4_h",
            controls,
            model_name=f"region_{region}",
        )
        model["subgroup_type"] = "UN_SDG_region"
        model["subgroup"] = region
        rows.append(model[model["term"].str.contains("storage_score")])
    high["period"] = np.where(high["year"] <= 2013, "2003-2013", "2014-2025")
    for period, subset in high.groupby("period", sort=True):
        model = twfe_cluster_ols(
            subset,
            "differential_decay_1e4_h",
            controls,
            model_name=f"period_{period}",
        )
        model["subgroup_type"] = "period"
        model["subgroup"] = period
        rows.append(model[model["term"].str.contains("storage_score")])
    return pd.concat(rows, ignore_index=True)


def component_models(frame: pd.DataFrame) -> pd.DataFrame:
    city = pd.read_csv(BUILT_FORM, dtype={"uc_id": str})
    high = frame[
        frame["high_green"].eq(1) & frame["analysis_state"].isin(STATES)
    ].merge(city[["uc_id", *BUILT_FORM_FEATURES]], on="uc_id", how="left")
    controls = [
        "is_dhd",
        "is_extreme_dhd",
        "z_t2m_true_night_pct_rank",
        "z_vpd_pct",
        "z_rzsm_pct",
    ]
    rows = []
    for feature in BUILT_FORM_FEATURES:
        z_feature = f"z_{feature}"
        high[z_feature] = (high[feature] - high[feature].mean()) / high[feature].std(ddof=0)
        high[f"dhd_x_{feature}"] = high["is_dhd"] * high[z_feature]
        high[f"extreme_x_{feature}"] = high["is_extreme_dhd"] * high[z_feature]
        model = twfe_cluster_ols(
            high,
            "differential_decay_1e4_h",
            [*controls, f"dhd_x_{feature}", f"extreme_x_{feature}"],
            model_name=feature,
        )
        rows.append(model[model["term"].str.contains(feature)])
    return pd.concat(rows, ignore_index=True)


def coupled_water_storage_models(
    frame: pd.DataFrame, city: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    water = pd.read_csv(BUILT_FORM, dtype={"uc_id": str})[
        ["uc_id", "mean_water_support_ratio"]
    ]
    city_water = city.merge(water, on="uc_id", how="left", validate="one_to_one")
    city_water["z_water_support"] = (
        city_water["mean_water_support_ratio"]
        - city_water["mean_water_support_ratio"].mean()
    ) / city_water["mean_water_support_ratio"].std(ddof=0)
    city_water["water_support_tertile"] = pd.qcut(
        city_water["mean_water_support_ratio"],
        3,
        labels=["Low", "Intermediate", "High"],
    )
    high = add_storage(
        frame[frame["high_green"].eq(1) & frame["analysis_state"].isin(STATES)].copy(),
        city_water,
    )
    high["dhd_x_water_support"] = high["is_dhd"] * high["z_water_support"]
    high["extreme_x_water_support"] = high["is_extreme_dhd"] * high["z_water_support"]
    high["dhd_x_storage_x_water_support"] = (
        high["is_dhd"] * high["built_form_storage_score"] * high["z_water_support"]
    )
    high["extreme_x_storage_x_water_support"] = (
        high["is_extreme_dhd"]
        * high["built_form_storage_score"]
        * high["z_water_support"]
    )
    controls = [
        "is_dhd",
        "is_extreme_dhd",
        "z_t2m_true_night_pct_rank",
        "z_vpd_pct",
        "z_rzsm_pct",
        "dhd_x_built_form_storage_score",
        "extreme_x_built_form_storage_score",
        "dhd_x_water_support",
        "extreme_x_water_support",
        "dhd_x_storage_x_water_support",
        "extreme_x_storage_x_water_support",
    ]
    coupled = twfe_cluster_ols(
        high,
        "differential_decay_1e4_h",
        controls,
        model_name="coupled_water_storage",
    )
    strata = []
    for tertile, subset in high.groupby("water_support_tertile", observed=True):
        model = twfe_cluster_ols(
            subset,
            "differential_decay_1e4_h",
            [
                "is_dhd",
                "is_extreme_dhd",
                "z_t2m_true_night_pct_rank",
                "z_vpd_pct",
                "z_rzsm_pct",
                "dhd_x_built_form_storage_score",
                "extreme_x_built_form_storage_score",
            ],
            model_name=f"water_support_{tertile}",
        )
        model["water_support_tertile"] = str(tertile)
        strata.append(model[model["term"].str.contains("storage_score")])
    return coupled, pd.concat(strata, ignore_index=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = prepare()
    pairs = pd.read_csv(PAIRS, dtype={"high_uc_id": str, "low_uc_id": str})
    city, _ = build_storage_score()
    random = np.random.default_rng(RANDOM_SEED)

    summary = pd.concat(
        [
            state_summary(frame, "all_intervals"),
            state_summary(
                frame[frame["heat_true_night_t2m_local_p90"].eq(1)],
                "true_night_heat_intervals",
            ),
        ],
        ignore_index=True,
    )
    matched = matched_contrasts(frame, pairs, random)
    terms = models(frame, city)
    sensitivity = sampling_sensitivity(frame, city)
    quartiles = storage_quartile_summary(frame, city)
    subgroups = subgroup_storage_models(frame, city)
    components = component_models(frame)
    coupled, water_strata = coupled_water_storage_models(frame, city)

    summary.to_csv(OUT / "differential_thermal_decay_state_summary.csv", index=False)
    matched.to_csv(OUT / "matched_differential_thermal_decay_results.csv", index=False)
    terms.to_csv(OUT / "differential_thermal_decay_twfe_terms.csv", index=False)
    sensitivity.to_csv(OUT / "differential_thermal_decay_sampling_sensitivity.csv", index=False)
    quartiles.to_csv(OUT / "differential_thermal_decay_storage_quartiles.csv", index=False)
    subgroups.to_csv(OUT / "differential_thermal_decay_subgroup_interactions.csv", index=False)
    components.to_csv(OUT / "built_form_component_interactions.csv", index=False)
    coupled.to_csv(OUT / "coupled_water_storage_interaction.csv", index=False)
    water_strata.to_csv(OUT / "differential_decay_water_support_heterogeneity.csv", index=False)

    print("Differential thermal-decay state summary (rates x 10^4 h^-1)")
    print(summary.round(5).to_string(index=False))
    print("\nMatched contrasts")
    print(matched.round(5).to_string(index=False))
    key = terms[terms["term"].str.contains("high_green|storage_score|ventilation|ahe", regex=True)]
    print("\nKey fixed-effect terms")
    print(key.round(5).to_string(index=False))
    print("\nSampling sensitivity")
    print(sensitivity.round(5).to_string(index=False))
    print("\nStorage-quartile dose response")
    print(quartiles.round(5).to_string(index=False))
    print("\nRegional and period stability")
    print(subgroups.round(5).to_string(index=False))
    print("\nIndividual built-form components")
    print(components.round(5).to_string(index=False))
    print("\nCoupled water-support and built-form model")
    print(coupled.round(5).to_string(index=False))
    print("\nBuilt-form moderation by water-support tertile")
    print(water_strata.round(5).to_string(index=False))


if __name__ == "__main__":
    main()
