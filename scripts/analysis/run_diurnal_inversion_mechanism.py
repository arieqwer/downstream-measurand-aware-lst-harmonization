from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_1samp
from sklearn.decomposition import PCA

from analysis_utils import bootstrap_mean_ci, twfe_cluster_ols


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/external/valid_city_interval_panel.parquet"
PAIRS = ROOT / "data/processed/analysis_outputs/optimal_exact_matched_pairs.csv"
BUILT_FORM = ROOT / "data/processed/urban_form_covariates.csv"
OUT = ROOT / "data/processed/analysis_outputs"
RANDOM_SEED = 20260714
STATES = ["mld", "dhd", "extreme_dhd"]
INVERSION_THRESHOLDS = [0.0, 0.1, 0.25, 0.5]
BUILT_FORM_FEATURES = [
    "built_surface_fraction_2020",
    "mean_building_height_2020",
    "road_density_2024",
    "lcz_compact_share_2025",
]


def prepare_panel() -> pd.DataFrame:
    columns = [
        "uc_id",
        "year",
        "time_id",
        "analysis_state",
        "high_green",
        "z_ring_green_support",
        "un_sdg_reg",
        "t2m_true_night_pct_rank",
        "heat_true_night_t2m_local_p90",
        "vpd_pct",
        "rzsm_pct",
        "core_minus_ring_tb_night_anom",
        "raw_core_minus_ring_tb_day_anom",
    ]
    frame = pd.read_parquet(PANEL, columns=columns)
    frame = frame.dropna(subset=["raw_core_minus_ring_tb_day_anom"]).copy()
    frame["day_gradient"] = frame["raw_core_minus_ring_tb_day_anom"]
    frame["night_gradient"] = frame["core_minus_ring_tb_night_anom"]
    frame["day_to_night_shift"] = frame["night_gradient"] - frame["day_gradient"]
    frame["is_dhd"] = frame["analysis_state"].eq("dhd").astype(float)
    frame["is_extreme_dhd"] = frame["analysis_state"].eq("extreme_dhd").astype(float)
    heat_mean = frame["t2m_true_night_pct_rank"].mean()
    heat_sd = frame["t2m_true_night_pct_rank"].std(ddof=0)
    frame["z_true_night_heat"] = (frame["t2m_true_night_pct_rank"] - heat_mean) / heat_sd
    for column in ["vpd_pct", "rzsm_pct"]:
        frame[f"z_{column}"] = (frame[column] - frame[column].mean()) / frame[column].std(ddof=0)
    for threshold in INVERSION_THRESHOLDS:
        label = str(threshold).replace(".", "p")
        frame[f"inversion_{label}"] = (
            frame["day_gradient"].lt(-threshold) & frame["night_gradient"].gt(threshold)
        ).astype("int8")
    return frame


def build_storage_score() -> tuple[pd.DataFrame, pd.DataFrame]:
    city = pd.read_csv(BUILT_FORM, dtype={"uc_id": str})
    standardized = (city[BUILT_FORM_FEATURES] - city[BUILT_FORM_FEATURES].mean()) / city[
        BUILT_FORM_FEATURES
    ].std(ddof=0)
    complete = standardized.notna().all(axis=1)
    pca = PCA(n_components=1)
    score = pd.Series(np.nan, index=city.index, dtype=float)
    score.loc[complete] = pca.fit_transform(standardized.loc[complete]).ravel()
    if pca.components_[0].sum() < 0:
        score.loc[complete] *= -1
        pca.components_[0] *= -1
    city["built_form_storage_score"] = (score - score.mean()) / score.std(ddof=0)

    for column in ["ventilation_obstruction_index", "ahe_night_wm2"]:
        city[f"z_{column}"] = (city[column] - city[column].mean()) / city[column].std(ddof=0)

    loadings = pd.DataFrame(
        {
            "feature": BUILT_FORM_FEATURES,
            "pc1_loading": pca.components_[0],
            "pc1_variance_explained": pca.explained_variance_ratio_[0],
            "n_complete_cities": int(complete.sum()),
        }
    )
    keep = [
        "uc_id",
        "built_form_storage_score",
        "z_ventilation_obstruction_index",
        "z_ahe_night_wm2",
    ]
    return city[keep], loadings


def state_summary(frame: pd.DataFrame, sample: str) -> pd.DataFrame:
    outcomes = [
        "day_gradient",
        "night_gradient",
        "day_to_night_shift",
        *[f"inversion_{str(value).replace('.', 'p')}" for value in INVERSION_THRESHOLDS],
    ]
    rows = []
    for (high_green, state), subset in frame[frame["analysis_state"].isin(STATES)].groupby(
        ["high_green", "analysis_state"], sort=True
    ):
        row = {
            "sample": sample,
            "high_green": int(high_green),
            "analysis_state": state,
            "n_paired_day_night_intervals": len(subset),
            "n_cities": subset["uc_id"].nunique(),
        }
        for outcome in outcomes:
            row[f"mean_{outcome}"] = subset[outcome].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def city_state_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    outcomes = [
        "day_gradient",
        "night_gradient",
        "day_to_night_shift",
        *[f"inversion_{str(value).replace('.', 'p')}" for value in INVERSION_THRESHOLDS],
    ]
    aggregation = {"n_intervals": ("time_id", "size")}
    aggregation.update({outcome: (outcome, "mean") for outcome in outcomes})
    return (
        frame[frame["analysis_state"].isin(STATES)]
        .groupby(["uc_id", "analysis_state"], as_index=False)
        .agg(**aggregation)
    )


def matched_state_contrasts(
    frame: pd.DataFrame, pairs: pd.DataFrame, random: np.random.Generator
) -> tuple[pd.DataFrame, pd.DataFrame]:
    city_state = city_state_metrics(frame)
    wide = city_state.pivot(index="uc_id", columns="analysis_state")
    outcomes = [
        "day_gradient",
        "night_gradient",
        "day_to_night_shift",
        *[f"inversion_{str(value).replace('.', 'p')}" for value in INVERSION_THRESHOLDS],
    ]
    summary_rows = []
    pair_rows = []
    for state in ["dhd", "extreme_dhd"]:
        for outcome in outcomes:
            values = pd.DataFrame(
                {
                    "uc_id": wide.index,
                    "state_shift": wide[(outcome, state)] - wide[(outcome, "mld")],
                    "n_mld": wide[("n_intervals", "mld")],
                    "n_stress": wide[("n_intervals", state)],
                }
            ).dropna()
            values = values[(values["n_mld"] >= 10) & (values["n_stress"] >= 10)].set_index("uc_id")
            matched = (
                pairs.merge(values[["state_shift"]], left_on="high_uc_id", right_index=True, how="inner")
                .rename(columns={"state_shift": "high_shift"})
                .merge(values[["state_shift"]], left_on="low_uc_id", right_index=True, how="inner")
                .rename(columns={"state_shift": "low_shift"})
            )
            matched["high_minus_low_shift"] = matched["high_shift"] - matched["low_shift"]
            differences = matched["high_minus_low_shift"].to_numpy(dtype=float)
            ci_low, ci_high = bootstrap_mean_ci(differences, random)
            test = ttest_1samp(differences, popmean=0.0)
            summary_rows.append(
                {
                    "contrast": f"{state}_minus_mld",
                    "outcome": outcome,
                    "n_pairs": len(matched),
                    "matched_high_minus_low_shift": differences.mean(),
                    "std_error": differences.std(ddof=1) / np.sqrt(len(differences)),
                    "bootstrap_ci95_low": ci_low,
                    "bootstrap_ci95_high": ci_high,
                    "p_value": test.pvalue,
                }
            )
            pair_rows.append(
                matched.assign(contrast=f"{state}_minus_mld", outcome=outcome)[
                    [
                        "high_uc_id",
                        "low_uc_id",
                        "contrast",
                        "outcome",
                        "high_shift",
                        "low_shift",
                        "high_minus_low_shift",
                    ]
                ]
            )
    return pd.DataFrame(summary_rows), pd.concat(pair_rows, ignore_index=True)


def add_external_interactions(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    merged = frame.merge(city, on="uc_id", how="left", validate="many_to_one")
    for feature in [
        "built_form_storage_score",
        "z_ventilation_obstruction_index",
        "z_ahe_night_wm2",
    ]:
        merged[f"dhd_x_{feature}"] = merged["is_dhd"] * merged[feature]
        merged[f"extreme_x_{feature}"] = merged["is_extreme_dhd"] * merged[feature]
    return merged


def diurnal_models(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    states = frame[frame["analysis_state"].isin(STATES)].copy()
    states["dhd_x_high_green"] = states["is_dhd"] * states["high_green"]
    states["extreme_x_high_green"] = states["is_extreme_dhd"] * states["high_green"]
    states["dhd_x_green_support"] = states["is_dhd"] * states["z_ring_green_support"]
    states["extreme_x_green_support"] = states["is_extreme_dhd"] * states["z_ring_green_support"]
    rows = [
        twfe_cluster_ols(
            states,
            "night_gradient",
            [
                "day_gradient",
                "is_dhd",
                "is_extreme_dhd",
                "z_true_night_heat",
                "z_vpd_pct",
                "z_rzsm_pct",
                "dhd_x_high_green",
                "extreme_x_high_green",
            ],
            model_name="paired_diurnal_binary_green",
        ),
        twfe_cluster_ols(
            states,
            "night_gradient",
            [
                "day_gradient",
                "is_dhd",
                "is_extreme_dhd",
                "z_true_night_heat",
                "z_vpd_pct",
                "z_rzsm_pct",
                "dhd_x_green_support",
                "extreme_x_green_support",
            ],
            model_name="paired_diurnal_continuous_green",
        ),
    ]

    high = add_external_interactions(states[states["high_green"].eq(1)].copy(), city)
    for feature in [
        "built_form_storage_score",
        "z_ventilation_obstruction_index",
        "z_ahe_night_wm2",
    ]:
        rows.append(
            twfe_cluster_ols(
                high,
                "night_gradient",
                [
                    "day_gradient",
                    "is_dhd",
                    "is_extreme_dhd",
                    "z_true_night_heat",
                    "z_vpd_pct",
                    "z_rzsm_pct",
                    f"dhd_x_{feature}",
                    f"extreme_x_{feature}",
                ],
                model_name=f"paired_diurnal_{feature}",
            )
        )
        for threshold in INVERSION_THRESHOLDS:
            label = str(threshold).replace(".", "p")
            rows.append(
                twfe_cluster_ols(
                    high,
                    f"inversion_{label}",
                    [
                        "is_dhd",
                        "is_extreme_dhd",
                        "z_true_night_heat",
                        "z_vpd_pct",
                        "z_rzsm_pct",
                        f"dhd_x_{feature}",
                        f"extreme_x_{feature}",
                    ],
                    model_name=f"inversion_{label}_{feature}",
                )
            )
    return pd.concat(rows, ignore_index=True)


def state_dependence_models(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    base = frame.sort_values(["uc_id", "time_id"]).copy()
    grouped = base.groupby("uc_id", sort=False)
    previous_time = grouped["time_id"].shift(1)
    base["prior_night_gradient"] = grouped["night_gradient"].shift(1).where(
        base["time_id"] - previous_time == 1
    )
    base = base[base["analysis_state"].isin(STATES) & base["prior_night_gradient"].notna()].copy()
    base = add_external_interactions(base, city)
    rows = []
    for threshold in INVERSION_THRESHOLDS:
        label = str(threshold).replace(".", "p")
        base["loss_state_dynamic"] = base["night_gradient"].gt(threshold).astype(float)
        base["prior_loss_state"] = base["prior_night_gradient"].gt(threshold).astype(float)
        base["dhd_x_prior_loss"] = base["is_dhd"] * base["prior_loss_state"]
        base["extreme_x_prior_loss"] = base["is_extreme_dhd"] * base["prior_loss_state"]
        rows.append(
            twfe_cluster_ols(
                base,
                "loss_state_dynamic",
                [
                    "is_dhd",
                    "is_extreme_dhd",
                    "prior_loss_state",
                    "dhd_x_prior_loss",
                    "extreme_x_prior_loss",
                    "z_true_night_heat",
                    "z_vpd_pct",
                    "z_rzsm_pct",
                ],
                model_name=f"state_dependence_threshold_{label}",
            )
        )
        for prior_state, transition in [(0.0, "onset"), (1.0, "persistence")]:
            subset = base[base["prior_loss_state"].eq(prior_state)]
            rows.append(
                twfe_cluster_ols(
                    subset,
                    "loss_state_dynamic",
                    [
                        "is_dhd",
                        "is_extreme_dhd",
                        "z_true_night_heat",
                        "z_vpd_pct",
                        "z_rzsm_pct",
                        "dhd_x_built_form_storage_score",
                        "extreme_x_built_form_storage_score",
                    ],
                    model_name=f"{transition}_storage_threshold_{label}",
                )
            )
    return pd.concat(rows, ignore_index=True)


def region_storage_models(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    high = frame[
        frame["high_green"].eq(1) & frame["analysis_state"].isin(["mld", "dhd"])
    ].copy()
    high = add_external_interactions(high, city)
    rows = []
    for region, subset in high.groupby("un_sdg_reg", sort=True):
        if subset["uc_id"].nunique() < 40:
            continue
        model = twfe_cluster_ols(
            subset,
            "night_gradient",
            [
                "day_gradient",
                "is_dhd",
                "z_true_night_heat",
                "z_vpd_pct",
                "z_rzsm_pct",
                "dhd_x_built_form_storage_score",
            ],
            model_name=f"region_{region}",
        )
        rows.append(model[model["term"].eq("dhd_x_built_form_storage_score")])
    return pd.concat(rows, ignore_index=True)


def period_storage_models(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    high = frame[
        frame["high_green"].eq(1) & frame["analysis_state"].isin(["mld", "dhd"])
    ].copy()
    high = add_external_interactions(high, city)
    periods = {
        "2003_2013": high[high["year"] <= 2013],
        "2014_2025": high[high["year"] >= 2014],
    }
    rows = []
    for period, subset in periods.items():
        model = twfe_cluster_ols(
            subset,
            "night_gradient",
            [
                "day_gradient",
                "is_dhd",
                "z_true_night_heat",
                "z_vpd_pct",
                "z_rzsm_pct",
                "dhd_x_built_form_storage_score",
            ],
            model_name=f"period_{period}",
        )
        rows.append(model[model["term"].eq("dhd_x_built_form_storage_score")])
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    random = np.random.default_rng(RANDOM_SEED)
    frame = prepare_panel()
    pairs = pd.read_csv(PAIRS, dtype={"high_uc_id": str, "low_uc_id": str})
    city, loadings = build_storage_score()

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
    matched_summary, matched_pairs = matched_state_contrasts(frame, pairs, random)
    diurnal_terms = diurnal_models(frame, city)
    dynamic_terms = state_dependence_models(frame[frame["high_green"].eq(1)].copy(), city)
    regional_terms = region_storage_models(frame, city)
    period_terms = period_storage_models(frame, city)

    summary.to_csv(OUT / "diurnal_inversion_state_summary.csv", index=False)
    matched_summary.to_csv(OUT / "matched_diurnal_inversion_results.csv", index=False)
    matched_pairs.to_csv(OUT / "matched_diurnal_inversion_pair_effects.csv", index=False)
    loadings.to_csv(OUT / "built_form_storage_score_loadings.csv", index=False)
    diurnal_terms.to_csv(OUT / "diurnal_inversion_twfe_terms.csv", index=False)
    dynamic_terms.to_csv(OUT / "state_dependence_twfe_terms.csv", index=False)
    regional_terms.to_csv(OUT / "regional_storage_interaction_terms.csv", index=False)
    period_terms.to_csv(OUT / "period_storage_interaction_terms.csv", index=False)

    print("Paired day-night state summary")
    print(summary.round(5).to_string(index=False))
    print("\nMatched inversion contrasts")
    print(matched_summary.round(5).to_string(index=False))
    print("\nStorage-score loadings")
    print(loadings.round(5).to_string(index=False))
    print("\nState-dependence terms")
    print(
        dynamic_terms[
            dynamic_terms["term"].isin(
                ["dhd_x_prior_loss", "extreme_x_prior_loss", "dhd_x_built_form_storage_score"]
            )
        ].round(5).to_string(index=False)
    )
    print("\nRegional storage interaction")
    print(regional_terms.round(5).to_string(index=False))


if __name__ == "__main__":
    main()
