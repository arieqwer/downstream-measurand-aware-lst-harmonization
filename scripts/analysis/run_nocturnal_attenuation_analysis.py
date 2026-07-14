from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_1samp

from analysis_utils import bootstrap_mean_ci, twfe_cluster_ols
from run_diurnal_inversion_mechanism import build_storage_score


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/external/valid_city_interval_panel.parquet"
PAIRS = ROOT / "data/processed/analysis_outputs/optimal_exact_matched_pairs.csv"
OUT = ROOT / "data/processed/analysis_outputs"
RANDOM_SEED = 20260714
STATES = ["mld", "dhd", "extreme_dhd"]


def prepare_panel() -> pd.DataFrame:
    columns = [
        "uc_id",
        "year",
        "time_id",
        "analysis_state",
        "high_green",
        "un_sdg_reg",
        "heat_true_night_t2m_local_p90",
        "t2m_true_night_pct_rank",
        "vpd_pct",
        "rzsm_pct",
        "core_tb_day",
        "ring_tb_day",
        "core_tb_night",
        "ring_tb_night",
        "core_tv_day",
        "ring_tv_day",
        "core_tv_night",
        "ring_tv_night",
    ]
    frame = pd.read_parquet(PANEL, columns=columns)
    for surface in ["tb", "tv"]:
        frame[f"{surface}_day_contrast"] = (
            frame[f"core_{surface}_day"] - frame[f"ring_{surface}_day"]
        )
        frame[f"{surface}_night_contrast"] = (
            frame[f"core_{surface}_night"] - frame[f"ring_{surface}_night"]
        )
        frame[f"{surface}_nocturnal_attenuation"] = (
            frame[f"{surface}_day_contrast"] - frame[f"{surface}_night_contrast"]
        )
    frame["is_dhd"] = frame["analysis_state"].eq("dhd").astype(float)
    frame["is_extreme_dhd"] = frame["analysis_state"].eq("extreme_dhd").astype(float)
    for column in ["t2m_true_night_pct_rank", "vpd_pct", "rzsm_pct"]:
        frame[f"z_{column}"] = (frame[column] - frame[column].mean()) / frame[column].std(ddof=0)
    return frame


def state_summary(frame: pd.DataFrame, sample: str) -> pd.DataFrame:
    outcomes = [
        "tb_day_contrast",
        "tb_night_contrast",
        "tb_nocturnal_attenuation",
        "tv_day_contrast",
        "tv_night_contrast",
        "tv_nocturnal_attenuation",
    ]
    paired = frame.dropna(subset=outcomes)
    rows = []
    for (high_green, state), subset in paired[paired["analysis_state"].isin(STATES)].groupby(
        ["high_green", "analysis_state"], sort=True
    ):
        row = {
            "sample": sample,
            "high_green": int(high_green),
            "analysis_state": state,
            "n_complete_intervals": len(subset),
            "n_cities": subset["uc_id"].nunique(),
        }
        for outcome in outcomes:
            row[f"mean_{outcome}"] = subset[outcome].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def city_state_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    outcomes = [
        "tb_day_contrast",
        "tb_night_contrast",
        "tb_nocturnal_attenuation",
        "tv_day_contrast",
        "tv_night_contrast",
        "tv_nocturnal_attenuation",
    ]
    return (
        frame[frame["analysis_state"].isin(STATES)]
        .groupby(["uc_id", "analysis_state"], as_index=False)
        .agg(
            n_intervals=("time_id", "size"),
            **{outcome: (outcome, "mean") for outcome in outcomes},
        )
    )


def matched_state_contrasts(
    frame: pd.DataFrame, pairs: pd.DataFrame, random: np.random.Generator
) -> pd.DataFrame:
    city_state = city_state_metrics(frame)
    wide = city_state.pivot(index="uc_id", columns="analysis_state")
    outcomes = [
        "tb_day_contrast",
        "tb_night_contrast",
        "tb_nocturnal_attenuation",
        "tv_day_contrast",
        "tv_night_contrast",
        "tv_nocturnal_attenuation",
    ]
    rows = []
    for state in ["dhd", "extreme_dhd"]:
        for outcome in outcomes:
            shifts = pd.DataFrame(
                {
                    "uc_id": wide.index,
                    "state_shift": wide[(outcome, state)] - wide[(outcome, "mld")],
                    "n_mld": wide[("n_intervals", "mld")],
                    "n_stress": wide[("n_intervals", state)],
                }
            ).dropna()
            shifts = shifts[(shifts["n_mld"] >= 10) & (shifts["n_stress"] >= 10)].set_index(
                "uc_id"
            )
            matched = (
                pairs.merge(shifts[["state_shift"]], left_on="high_uc_id", right_index=True)
                .rename(columns={"state_shift": "high_shift"})
                .merge(shifts[["state_shift"]], left_on="low_uc_id", right_index=True)
                .rename(columns={"state_shift": "low_shift"})
            )
            effect = (matched["high_shift"] - matched["low_shift"]).to_numpy(dtype=float)
            ci_low, ci_high = bootstrap_mean_ci(effect, random)
            test = ttest_1samp(effect, popmean=0.0)
            rows.append(
                {
                    "contrast": f"{state}_minus_mld",
                    "outcome": outcome,
                    "n_pairs": len(effect),
                    "matched_high_minus_low_shift": effect.mean(),
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


def fixed_effect_models(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    states = frame[frame["analysis_state"].isin(STATES)].copy()
    states["dhd_x_high_green"] = states["is_dhd"] * states["high_green"]
    states["extreme_x_high_green"] = states["is_extreme_dhd"] * states["high_green"]
    controls = [
        "is_dhd",
        "is_extreme_dhd",
        "z_t2m_true_night_pct_rank",
        "z_vpd_pct",
        "z_rzsm_pct",
    ]
    models = [
        twfe_cluster_ols(
            states,
            "tb_night_contrast",
            [
                "tb_day_contrast",
                *controls,
                "dhd_x_high_green",
                "extreme_x_high_green",
            ],
            model_name="raw_contrast_high_green",
        )
    ]

    high = add_storage(states[states["high_green"].eq(1)].copy(), city)
    for feature in [
        "built_form_storage_score",
        "z_ventilation_obstruction_index",
        "z_ahe_night_wm2",
    ]:
        models.append(
            twfe_cluster_ols(
                high,
                "tb_night_contrast",
                [
                    "tb_day_contrast",
                    *controls,
                    f"dhd_x_{feature}",
                    f"extreme_x_{feature}",
                ],
                model_name=f"raw_contrast_{feature}",
            )
        )
    return pd.concat(models, ignore_index=True)


def storage_dose_response(frame: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    high = frame[frame["high_green"].eq(1)].merge(
        city[["uc_id", "built_form_storage_score"]], on="uc_id", how="left", validate="many_to_one"
    )
    city_scores = city.dropna(subset=["built_form_storage_score"]).copy()
    city_scores["storage_quartile"] = pd.qcut(
        city_scores["built_form_storage_score"], 4, labels=[1, 2, 3, 4]
    ).astype(int)
    high = high.drop(columns="built_form_storage_score").merge(
        city_scores[["uc_id", "built_form_storage_score", "storage_quartile"]],
        on="uc_id",
        how="inner",
        validate="many_to_one",
    )
    city_state = (
        high[high["analysis_state"].isin(STATES)]
        .groupby(["uc_id", "storage_quartile", "analysis_state"], as_index=False)
        .agg(
            n_intervals=("time_id", "size"),
            tb_nocturnal_attenuation=("tb_nocturnal_attenuation", "mean"),
            tb_night_contrast=("tb_night_contrast", "mean"),
        )
    )
    wide = city_state.pivot(index=["uc_id", "storage_quartile"], columns="analysis_state")
    result = pd.DataFrame(
        {
            "dhd_minus_mld_attenuation": wide[("tb_nocturnal_attenuation", "dhd")]
            - wide[("tb_nocturnal_attenuation", "mld")],
            "dhd_minus_mld_night_contrast": wide[("tb_night_contrast", "dhd")]
            - wide[("tb_night_contrast", "mld")],
            "n_mld": wide[("n_intervals", "mld")],
            "n_dhd": wide[("n_intervals", "dhd")],
        },
        index=wide.index,
    ).reset_index()
    result = result[(result["n_mld"] >= 10) & (result["n_dhd"] >= 10)]
    return (
        result.groupby("storage_quartile", as_index=False)
        .agg(
            n_cities=("uc_id", "nunique"),
            mean_dhd_minus_mld_attenuation=("dhd_minus_mld_attenuation", "mean"),
            se_dhd_minus_mld_attenuation=("dhd_minus_mld_attenuation", "sem"),
            mean_dhd_minus_mld_night_contrast=("dhd_minus_mld_night_contrast", "mean"),
            se_dhd_minus_mld_night_contrast=("dhd_minus_mld_night_contrast", "sem"),
        )
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    random = np.random.default_rng(RANDOM_SEED)
    frame = prepare_panel()
    pairs = pd.read_csv(PAIRS, dtype={"high_uc_id": str, "low_uc_id": str})
    city, _ = build_storage_score()

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
    matched = matched_state_contrasts(frame, pairs, random)
    model_terms = fixed_effect_models(frame, city)
    dose_response = storage_dose_response(frame, city)

    summary.to_csv(OUT / "raw_nocturnal_attenuation_state_summary.csv", index=False)
    matched.to_csv(OUT / "matched_raw_nocturnal_attenuation_results.csv", index=False)
    model_terms.to_csv(OUT / "raw_nocturnal_attenuation_twfe_terms.csv", index=False)
    dose_response.to_csv(OUT / "storage_dose_response.csv", index=False)

    print("Raw nocturnal attenuation state summary")
    print(summary.round(5).to_string(index=False))
    print("\nMatched state contrasts")
    print(matched.round(5).to_string(index=False))
    key_terms = model_terms[
        model_terms["term"].str.contains("high_green|storage_score|ventilation|ahe", regex=True)
    ]
    print("\nKey fixed-effect terms")
    print(key_terms.round(5).to_string(index=False))
    print("\nStorage dose response")
    print(dose_response.round(5).to_string(index=False))


if __name__ == "__main__":
    main()
