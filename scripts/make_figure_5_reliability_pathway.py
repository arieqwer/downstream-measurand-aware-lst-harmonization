from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from nature_figure_style import add_panel_label, despine, save_figure, set_nature_style


REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = REPO_ROOT / "data" / "processed"
PANEL_IN = PROCESSED / "not_included" / "true_night_green_refuge_failure_panel.parquet"
WATER_IN = PROCESSED / "not_included" / "terraclimate_city_month_water_support.csv"
GREEN_IN = PROCESSED / "metadata" / "panel_city_base_corrected.csv"
BUILTFORM_IN = PROCESSED / "not_included" / "survivor_city_feature_table_builtform.csv"
AH_IN = PROCESSED / "not_included" / "ah4guc_city_anthropogenic_heat.csv"
ONSET_FIT_IN = PROCESSED / "extended_outputs_local" / "60_true_night_failure_onset_attribution" / "failure_onset_attribution_model_fit.csv"
ONSET_CURVE_IN = PROCESSED / "extended_outputs_local" / "59_true_night_failure_onset_event_study" / "failure_onset_curve_summary.csv"

OUT = PROCESSED / "extended_outputs_local" / "72_green_refuge_reliability_pathway"
FIG_OUT = REPO_ROOT / "outputs" / "figures" / "main"

GREEN_DARK = "#276749"
GREEN_LIGHT = "#98c379"
RED = "#c23b22"
BLUE = "#2b6cb0"
GOLD = "#d4a017"
TEAL = "#2a9d8f"
SLATE = "#4b5563"


def interval_month(year: pd.Series, step8: pd.Series) -> pd.Series:
    dates = pd.to_datetime(year.astype(str) + "-01-01") + pd.to_timedelta((step8.astype(int) - 1) * 8, unit="D")
    return dates.dt.month.astype(int)


def zscore(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    std = s.std()
    return (s - s.mean()) / std if pd.notna(std) and std > 0 else s * np.nan


def zscore_by_group(df: pd.DataFrame, value: str, group: str = "un_sdg_reg") -> pd.Series:
    return df.groupby(group, observed=True)[value].transform(zscore)


def sigmoid(x: np.ndarray | pd.Series) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))


def logit(p: np.ndarray | pd.Series) -> np.ndarray:
    arr = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(arr / (1 - arr))


def auc_score(y: np.ndarray | pd.Series, pred: np.ndarray | pd.Series) -> float:
    y = np.asarray(y, dtype=int)
    pred = np.asarray(pred, dtype=float)
    ok = np.isfinite(pred)
    y = y[ok]
    pred = pred[ok]
    if len(np.unique(y)) < 2:
        return np.nan
    order = np.argsort(pred)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(pred) + 1)
    # Average ranks for ties.
    vals, inv, counts = np.unique(pred, return_inverse=True, return_counts=True)
    if np.any(counts > 1):
        sums = np.bincount(inv, weights=ranks)
        avg = sums / counts
        ranks = avg[inv]
    n_pos = y.sum()
    n_neg = len(y) - n_pos
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def brier_score(y: np.ndarray | pd.Series, pred: np.ndarray | pd.Series) -> float:
    y = np.asarray(y, dtype=float)
    pred = np.clip(np.asarray(pred, dtype=float), 1e-6, 1 - 1e-6)
    return float(np.mean((pred - y) ** 2))


def calibration_slope(y: np.ndarray | pd.Series, pred: np.ndarray | pd.Series) -> float:
    y = np.asarray(y, dtype=float)
    pred = np.clip(np.asarray(pred, dtype=float), 1e-6, 1 - 1e-6)
    if len(np.unique(y)) < 2:
        return np.nan
    data = pd.DataFrame({"y": y, "lp": logit(pred)}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(data) < 50:
        return np.nan
    try:
        fit = sm.GLM(data["y"], sm.add_constant(data["lp"]), family=sm.families.Binomial()).fit(maxiter=100, disp=0)
        return float(fit.params["lp"])
    except Exception:
        return np.nan


def metrics_for_predictions(df: pd.DataFrame, pred: np.ndarray | pd.Series, label: str) -> dict:
    return {
        "sample": label,
        "n_obs": int(len(df)),
        "event_rate": float(df["failure"].mean()) if len(df) else np.nan,
        "mean_pred": float(np.mean(pred)) if len(df) else np.nan,
        "auc": auc_score(df["failure"], pred),
        "brier": brier_score(df["failure"], pred),
        "calibration_slope": calibration_slope(df["failure"], pred),
    }


def build_pathway_panel() -> pd.DataFrame:
    cols = [
        "uc_id",
        "veg_group",
        "year",
        "step8",
        "time_id",
        "state",
        "dhd",
        "mld",
        "extreme_dhd",
        "rzsm_pct",
        "vpd_pct",
        "anomalous_core_warmer",
        "core_minus_ring_tb_night_anom",
        "population_2025",
        "un_sdg_reg",
        "wb_income",
        "t2m_true_night_c",
        "wetbulb_true_night_c",
        "heat_true_night_t2m_local_p90",
        "true_green_refuge_failure_local_t2m_p90",
    ]
    panel = pd.read_parquet(PANEL_IN, columns=cols)
    panel["uc_id"] = panel["uc_id"].astype(str)
    panel["month"] = interval_month(panel["year"], panel["step8"])
    panel["failure"] = panel["true_green_refuge_failure_local_t2m_p90"].fillna(0).astype(int)
    panel["dhd_hot"] = (panel["dhd"].eq(1) & panel["heat_true_night_t2m_local_p90"].eq(1)).astype(int)
    panel = panel.sort_values(["uc_id", "time_id"])
    panel["lag1_core_ring_built"] = panel.groupby("uc_id", observed=True)["core_minus_ring_tb_night_anom"].shift(1)
    panel["lag2_core_ring_built"] = panel.groupby("uc_id", observed=True)["core_minus_ring_tb_night_anom"].shift(2)

    water = pd.read_csv(WATER_IN, dtype={"uc_id": str})
    panel = panel.merge(water[["uc_id", "year", "month", "aet", "def", "water_support_ratio"]], on=["uc_id", "year", "month"], how="left")

    green = pd.read_csv(GREEN_IN, dtype={"uc_id": str}).rename(columns={"mean_ring_veg": "ring_green_support"})
    built = pd.read_csv(BUILTFORM_IN, dtype={"uc_id": str})
    ah = pd.read_csv(AH_IN, dtype={"uc_id": str})
    panel = panel.merge(green[["uc_id", "ring_green_support"]], on="uc_id", how="left")
    panel = panel.merge(
        built[
            [
                "uc_id",
                "built_surface_fraction_2020",
                "mean_building_height_2020",
                "road_density_2024",
                "lcz_compact_share_2025",
                "lcz_open_share_2025",
                "lcz_natural_share_2025",
                "green_cover_mean_2020",
            ]
        ],
        on="uc_id",
        how="left",
    )
    panel = panel.merge(ah[["uc_id", "ahe_night_wm2", "ahe_annual_wm2"]], on="uc_id", how="left")

    # Region-standardized indices keep the method interpretable while avoiding
    # a broad arid-versus-humid city contrast masquerading as mechanism.
    panel["z_green_support_region"] = zscore_by_group(panel, "ring_green_support")
    panel["z_water_support_region"] = zscore_by_group(panel, "water_support_ratio")
    panel["green_water_mismatch"] = panel["z_green_support_region"] - panel["z_water_support_region"]

    panel["z_lag1_built_retention_region"] = zscore_by_group(panel, "lag1_core_ring_built")
    panel["z_lag2_built_retention_region"] = zscore_by_group(panel, "lag2_core_ring_built")
    panel["antecedent_nocturnal_retention"] = panel[["z_lag1_built_retention_region", "z_lag2_built_retention_region"]].mean(axis=1)

    for col in [
        "lcz_compact_share_2025",
        "mean_building_height_2020",
        "built_surface_fraction_2020",
        "lcz_open_share_2025",
        "lcz_natural_share_2025",
        "ahe_night_wm2",
        "t2m_true_night_c",
        "vpd_pct",
        "rzsm_pct",
    ]:
        panel[f"z_{col}"] = zscore(panel[col])

    panel["ventilation_obstruction_index"] = (
        panel["z_lcz_compact_share_2025"]
        + panel["z_mean_building_height_2020"]
        + panel["z_built_surface_fraction_2020"]
        - panel["z_lcz_open_share_2025"]
        - panel["z_lcz_natural_share_2025"]
    )
    panel["z_ventilation_obstruction_index"] = zscore(panel["ventilation_obstruction_index"])
    panel["z_ahe_night_wm2"] = zscore(panel["ahe_night_wm2"])
    panel["z_t2m_true_night_c"] = zscore(panel["t2m_true_night_c"])
    panel["z_vpd_pct"] = zscore(panel["vpd_pct"])
    panel["z_rzsm_pct"] = zscore(panel["rzsm_pct"])
    panel["step8_cat"] = panel["step8"].astype(int).astype(str)
    return panel


MAIN_FORMULA = (
    "failure ~ green_water_mismatch + antecedent_nocturnal_retention + "
    "z_ventilation_obstruction_index + z_t2m_true_night_c + z_vpd_pct + z_rzsm_pct + "
    "C(un_sdg_reg) + C(wb_income)"
)

AH_FORMULA = (
    "failure ~ green_water_mismatch + antecedent_nocturnal_retention + "
    "z_ventilation_obstruction_index + z_ahe_night_wm2 + "
    "z_t2m_true_night_c + z_vpd_pct + z_rzsm_pct + C(un_sdg_reg) + C(wb_income)"
)

MODEL_COLS = [
    "failure",
    "green_water_mismatch",
    "antecedent_nocturnal_retention",
    "z_ventilation_obstruction_index",
    "z_t2m_true_night_c",
    "z_vpd_pct",
    "z_rzsm_pct",
    "un_sdg_reg",
    "wb_income",
    "population_2025",
    "year",
    "uc_id",
]


def fit_glm(formula: str, data: pd.DataFrame):
    return smf.glm(formula, data=data, family=sm.families.Binomial()).fit(maxiter=100, disp=0)


def model_rows(fit, model: str, n_obs: int) -> list[dict]:
    rows = []
    for term in fit.params.index:
        rows.append(
            {
                "model": model,
                "term": term,
                "coef_logit": float(fit.params[term]),
                "std_err": float(fit.bse[term]),
                "p_value": float(fit.pvalues[term]),
                "n_obs": int(n_obs),
                "aic": float(fit.aic),
            }
        )
    return rows


def average_marginal_effect(fit, data: pd.DataFrame, variable: str, delta: float = 1.0) -> float:
    base = np.asarray(fit.predict(data), dtype=float)
    shifted = data.copy()
    shifted[variable] = shifted[variable] + delta
    pred = np.asarray(fit.predict(shifted), dtype=float)
    return float(np.mean(pred - base))


def fit_main_models(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, object, pd.DataFrame]:
    target = panel[
        panel["veg_group"].eq("high_veg") & panel["dhd_hot"].eq(1)
    ].dropna(subset=MODEL_COLS).copy()
    fit = fit_glm(MAIN_FORMULA, target)
    pred = fit.predict(target)
    perf_rows = [metrics_for_predictions(target, pred, "target_high_green_dhd_hot_all_years")]

    term_rows = model_rows(fit, "main_pathway_high_green_dhd_hot", len(target))
    ame_rows = []
    for var in ["green_water_mismatch", "antecedent_nocturnal_retention", "z_ventilation_obstruction_index"]:
        ame_rows.append(
            {
                "model": "main_pathway_high_green_dhd_hot",
                "variable": var,
                "average_marginal_effect_probability_points_per_1sd": average_marginal_effect(fit, target, var, 1.0),
                "n_obs": int(len(target)),
            }
        )

    ah_cols = MODEL_COLS + ["z_ahe_night_wm2"]
    ah_target = panel[
        panel["veg_group"].eq("high_veg") & panel["dhd_hot"].eq(1)
    ].dropna(subset=ah_cols).copy()
    if len(ah_target) > 500 and ah_target["failure"].nunique() > 1:
        ah_fit = fit_glm(AH_FORMULA, ah_target)
        term_rows.extend(model_rows(ah_fit, "ahe_subset_pathway_high_green_dhd_hot", len(ah_target)))
        perf_rows.append(metrics_for_predictions(ah_target, ah_fit.predict(ah_target), "ahe_subset_high_green_dhd_hot"))
        ame_rows.append(
            {
                "model": "ahe_subset_pathway_high_green_dhd_hot",
                "variable": "z_ahe_night_wm2",
                "average_marginal_effect_probability_points_per_1sd": average_marginal_effect(ah_fit, ah_target, "z_ahe_night_wm2", 1.0),
                "n_obs": int(len(ah_target)),
            }
        )
    return pd.DataFrame(term_rows), pd.DataFrame(perf_rows), pd.DataFrame(ame_rows), fit, target


def validation_tests(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    cal_rows = []
    target = panel[
        panel["veg_group"].eq("high_veg") & panel["dhd_hot"].eq(1)
    ].dropna(subset=MODEL_COLS).copy()

    train = target[target["year"].le(2016)].copy()
    test = target[target["year"].ge(2017)].copy()
    if len(train) > 500 and len(test) > 500 and train["failure"].nunique() > 1 and test["failure"].nunique() > 1:
        fit = fit_glm(MAIN_FORMULA, train)
        pred = fit.predict(test)
        rows.append(metrics_for_predictions(test, pred, "out_of_time_train_2003_2016_test_2017_2025"))
        cal_rows.extend(decile_calibration(test, pred, "out_of_time"))

    for region in sorted(target["un_sdg_reg"].dropna().unique()):
        held = target[target["un_sdg_reg"].eq(region)].copy()
        train = target[~target["un_sdg_reg"].eq(region)].copy()
        if len(held) < 300 or held["failure"].nunique() < 2 or train["failure"].nunique() < 2:
            continue
        formula = (
            "failure ~ green_water_mismatch + antecedent_nocturnal_retention + "
            "z_ventilation_obstruction_index + z_t2m_true_night_c + z_vpd_pct + z_rzsm_pct + C(wb_income)"
        )
        fit = fit_glm(formula, train)
        pred = fit.predict(held)
        row = metrics_for_predictions(held, pred, f"leave_region_out::{region}")
        row["held_out_region"] = region
        rows.append(row)

    # Negative-control states: the same predictor architecture should be most
    # informative in the DHD true-hot state, not in benign moist or non-hot states.
    controls = {
        "negative_control_high_green_mld": panel["veg_group"].eq("high_veg") & panel["mld"].eq(1),
        "negative_control_high_green_dhd_non_hot": panel["veg_group"].eq("high_veg") & panel["dhd"].eq(1) & panel["heat_true_night_t2m_local_p90"].eq(0),
        "comparator_low_green_dhd_hot": panel["veg_group"].eq("low_veg") & panel["dhd_hot"].eq(1),
    }
    for label, mask in controls.items():
        data = panel[mask].dropna(subset=MODEL_COLS).copy()
        # Recast the outcome as anomalous core warming where DHD is absent, because
        # the full failure gate is defined to require DHD.
        if "mld" in label or "non_hot" in label:
            data["failure"] = data["anomalous_core_warmer"].astype(int)
        if len(data) < 1000 or data["failure"].nunique() < 2:
            continue
        fit = fit_glm(MAIN_FORMULA, data)
        pred = fit.predict(data)
        rows.append(metrics_for_predictions(data, pred, label))
    return pd.DataFrame(rows), pd.DataFrame(cal_rows)


def decile_calibration(df: pd.DataFrame, pred: np.ndarray | pd.Series, label: str) -> list[dict]:
    d = df.copy()
    d["pred"] = np.asarray(pred, dtype=float)
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=["pred", "failure"])
    try:
        d["decile"] = pd.qcut(d["pred"], q=10, labels=False, duplicates="drop") + 1
    except ValueError:
        return []
    rows = []
    for decile, sub in d.groupby("decile", observed=True):
        rows.append(
            {
                "validation": label,
                "decile": int(decile),
                "n_obs": int(len(sub)),
                "mean_pred": float(sub["pred"].mean()),
                "observed_failure_rate": float(sub["failure"].mean()),
            }
        )
    return rows


def counterfactual_resets(fit, target: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    obs = np.asarray(fit.predict(target), dtype=float)
    reset_specs = {
        "water_mismatch_to_regional_p25": ("green_water_mismatch", 0.25),
        "retention_to_regional_p25": ("antecedent_nocturnal_retention", 0.25),
        "obstruction_to_regional_p25": ("z_ventilation_obstruction_index", 0.25),
    }
    rows = []
    pred_table = target[["uc_id", "year", "step8", "population_2025", "un_sdg_reg", "failure"]].copy()
    pred_table["p_observed"] = obs
    for label, (var, q) in reset_specs.items():
        cf = target.copy()
        regional_q = cf.groupby("un_sdg_reg", observed=True)[var].transform(lambda s: s.quantile(q))
        cf[var] = np.minimum(cf[var], regional_q)
        pred = np.asarray(fit.predict(cf), dtype=float)
        delta = np.maximum(obs - pred, 0)
        pred_table[f"p_{label}"] = pred
        pred_table[f"delta_{label}"] = delta
        rows.append(
            {
                "reset": label,
                "mean_probability_reduction": float(delta.mean()),
                "median_probability_reduction": float(np.median(delta)),
                "represented_resident_8day_intervals": float(np.sum(delta * target["population_2025"].to_numpy())),
                "n_obs": int(len(target)),
            }
        )

    joint = target.copy()
    for var, q in reset_specs.values():
        regional_q = joint.groupby("un_sdg_reg", observed=True)[var].transform(lambda s: s.quantile(q))
        joint[var] = np.minimum(joint[var], regional_q)
    pred = np.asarray(fit.predict(joint), dtype=float)
    delta = np.maximum(obs - pred, 0)
    pred_table["p_joint_water_retention_obstruction"] = pred
    pred_table["delta_joint_water_retention_obstruction"] = delta
    rows.append(
        {
            "reset": "joint_water_retention_obstruction_to_regional_p25",
            "mean_probability_reduction": float(delta.mean()),
            "median_probability_reduction": float(np.median(delta)),
            "represented_resident_8day_intervals": float(np.sum(delta * target["population_2025"].to_numpy())),
            "n_obs": int(len(target)),
        }
    )
    return pd.DataFrame(rows), pred_table


def response_surface(fit, target: pd.DataFrame) -> pd.DataFrame:
    base = target.copy()
    rows = []
    gwmi_vals = np.linspace(base["green_water_mismatch"].quantile(0.05), base["green_water_mismatch"].quantile(0.95), 35)
    nri_vals = np.linspace(base["antecedent_nocturnal_retention"].quantile(0.05), base["antecedent_nocturnal_retention"].quantile(0.95), 35)
    obs_levels = {
        "low_obstruction": base["z_ventilation_obstruction_index"].quantile(0.25),
        "high_obstruction": base["z_ventilation_obstruction_index"].quantile(0.75),
    }
    # Use modal categories and median continuous controls so the surface is an
    # interpretable partial-dependence view, not a new city-level estimate.
    template = base.iloc[[0]].copy()
    template["un_sdg_reg"] = base["un_sdg_reg"].mode().iloc[0]
    template["wb_income"] = base["wb_income"].mode().iloc[0]
    template["z_t2m_true_night_c"] = base["z_t2m_true_night_c"].median()
    template["z_vpd_pct"] = base["z_vpd_pct"].median()
    template["z_rzsm_pct"] = base["z_rzsm_pct"].median()
    for obs_label, obs_val in obs_levels.items():
        for gwmi in gwmi_vals:
            for nri in nri_vals:
                row = template.copy()
                row["green_water_mismatch"] = gwmi
                row["antecedent_nocturnal_retention"] = nri
                row["z_ventilation_obstruction_index"] = obs_val
                rows.append(
                    {
                        "obstruction_level": obs_label,
                        "green_water_mismatch": float(gwmi),
                        "antecedent_nocturnal_retention": float(nri),
                        "predicted_failure_probability": float(fit.predict(row).iloc[0]),
                    }
                )
    return pd.DataFrame(rows)


def pathway_profile_predictions(fit, target: pd.DataFrame) -> pd.DataFrame:
    """Predicted probabilities for a simple cumulative pathway-risk staircase."""
    base = target.copy()
    template = base.iloc[[0]].copy()
    template["un_sdg_reg"] = base["un_sdg_reg"].mode().iloc[0]
    template["wb_income"] = base["wb_income"].mode().iloc[0]
    template["z_t2m_true_night_c"] = base["z_t2m_true_night_c"].median()
    template["z_vpd_pct"] = base["z_vpd_pct"].median()
    template["z_rzsm_pct"] = base["z_rzsm_pct"].median()

    q = {
        "gw_low": base["green_water_mismatch"].quantile(0.25),
        "gw_high": base["green_water_mismatch"].quantile(0.75),
        "ret_low": base["antecedent_nocturnal_retention"].quantile(0.25),
        "ret_high": base["antecedent_nocturnal_retention"].quantile(0.75),
        "obs_low": base["z_ventilation_obstruction_index"].quantile(0.25),
        "obs_high": base["z_ventilation_obstruction_index"].quantile(0.75),
    }
    specs = [
        ("Lower-risk", q["gw_low"], q["ret_low"], q["obs_low"]),
        ("Add\nmismatch", q["gw_high"], q["ret_low"], q["obs_low"]),
        ("Add\nretention", q["gw_high"], q["ret_high"], q["obs_low"]),
        ("Add\nobstruction", q["gw_high"], q["ret_high"], q["obs_high"]),
    ]
    rows = []
    for label, gwmi, retention, obstruction in specs:
        row = template.copy()
        row["green_water_mismatch"] = gwmi
        row["antecedent_nocturnal_retention"] = retention
        row["z_ventilation_obstruction_index"] = obstruction
        rows.append(
            {
                "profile": label,
                "green_water_mismatch": float(gwmi),
                "antecedent_nocturnal_retention": float(retention),
                "z_ventilation_obstruction_index": float(obstruction),
                "predicted_failure_probability": float(fit.predict(row).iloc[0]),
            }
        )
    return pd.DataFrame(rows)


def water_support_profile_check(panel: pd.DataFrame) -> pd.DataFrame:
    """Check whether high-green failure risk is attenuated under high water support.

    The TerraClimate water-support inputs used here currently cover the
    high-green-support process-validation sample, so this is framed as a
    within-high-green conditioning check rather than a high-versus-low-green
    interaction model.
    """
    sample = panel[
        panel["dhd_hot"].eq(1)
        & panel["veg_group"].eq("high_veg")
    ].dropna(
        subset=[
            "failure",
            "water_support_ratio",
            "z_t2m_true_night_c",
            "z_vpd_pct",
            "z_rzsm_pct",
            "un_sdg_reg",
            "wb_income",
            "population_2025",
        ]
    ).copy()
    q33 = sample.groupby("un_sdg_reg", observed=True)["water_support_ratio"].transform(lambda s: s.quantile(0.33))
    q67 = sample.groupby("un_sdg_reg", observed=True)["water_support_ratio"].transform(lambda s: s.quantile(0.67))
    sample["water_profile"] = np.where(
        sample["water_support_ratio"] <= q33,
        "low_water_support",
        np.where(sample["water_support_ratio"] >= q67, "high_water_support", "middle_water_support"),
    )
    sample = sample[sample["water_profile"].isin(["low_water_support", "high_water_support"])].copy()
    sample["low_water_support"] = sample["water_profile"].eq("low_water_support").astype(int)
    fit = smf.glm(
        "failure ~ low_water_support + z_t2m_true_night_c + z_vpd_pct + z_rzsm_pct + "
        "C(un_sdg_reg) + C(wb_income)",
        data=sample,
        family=sm.families.Binomial(),
    ).fit(maxiter=100, disp=0)

    base = sample.iloc[[0]].copy()
    base["un_sdg_reg"] = sample["un_sdg_reg"].mode().iloc[0]
    base["wb_income"] = sample["wb_income"].mode().iloc[0]
    for col in ["z_t2m_true_night_c", "z_vpd_pct", "z_rzsm_pct"]:
        base[col] = sample[col].median()

    rows = []
    for profile, low_flag in [("high_water_support", 0), ("low_water_support", 1)]:
        row = base.copy()
        row["low_water_support"] = low_flag
        subset = sample[sample["water_profile"].eq(profile)]
        rows.append(
            {
                "profile": profile,
                "n_obs": int(len(subset)),
                "observed_failure_share": float(subset["failure"].mean()),
                "population_weighted_failure_share": float(
                    np.average(subset["failure"], weights=subset["population_2025"])
                ),
                "adjusted_predicted_failure_probability": float(fit.predict(row).iloc[0]),
                "model_logit_low_water_coef": float(fit.params["low_water_support"]),
                "model_low_water_p_value": float(fit.pvalues["low_water_support"]),
            }
        )
    return pd.DataFrame(rows)


def make_pathway_figure(
    terms: pd.DataFrame,
    ame: pd.DataFrame,
    resets: pd.DataFrame,
    validation: pd.DataFrame,
    calibration: pd.DataFrame,
    surface: pd.DataFrame,
    profiles: pd.DataFrame,
) -> Path:
    set_nature_style()
    fig = plt.figure(figsize=(7.25, 6.2))
    gs = fig.add_gridspec(2, 2, hspace=0.62, wspace=0.48)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    # a, method schematic.
    ax_a.axis("off")
    ax_a.set_xlim(0, 1)
    ax_a.set_ylim(0, 1)
    boxes = [
        (0.02, 0.68, 0.29, 0.18, "Dry-high-\ndemand"),
        (0.36, 0.68, 0.27, 0.18, "True-night\nheat"),
        (0.69, 0.68, 0.29, 0.18, "Core-ring\nwarming"),
        (0.19, 0.30, 0.28, 0.18, "Green-water\nmismatch"),
        (0.54, 0.30, 0.28, 0.18, "Antecedent\nretention"),
    ]
    for x, y, w, h, text in boxes:
        patch = plt.Rectangle((x, y), w, h, facecolor="#edf2f7", edgecolor=SLATE, linewidth=0.8)
        ax_a.add_patch(patch)
        ax_a.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7)
    ax_a.text(0.33, 0.77, "+", ha="center", va="center", fontsize=12, fontweight="bold")
    ax_a.text(0.66, 0.77, "+", ha="center", va="center", fontsize=12, fontweight="bold")
    ax_a.annotate("", xy=(0.50, 0.54), xytext=(0.50, 0.66), arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=0.9))
    ax_a.text(0.57, 0.60, "failure gate", ha="left", va="center", fontsize=7, color=SLATE)
    ax_a.annotate("", xy=(0.33, 0.22), xytext=(0.33, 0.30), arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=0.9))
    ax_a.annotate("", xy=(0.68, 0.22), xytext=(0.68, 0.30), arrowprops=dict(arrowstyle="-|>", color=SLATE, lw=0.9))
    ax_a.text(0.50, 0.15, "Reliability-pathway model", ha="center", va="center", fontsize=8, fontweight="bold")
    add_panel_label(ax_a, "a", x=-0.10, y=1.10)

    # b, cumulative risk profiles. This replaces the earlier heat map with a
    # simpler visual statement of what the pathway model adds.
    profile_vals = profiles["predicted_failure_probability"].to_numpy()
    colors_b = [GREEN_LIGHT, GREEN_DARK, RED, GOLD]
    ax_b.bar(np.arange(len(profile_vals)), profile_vals, color=colors_b, width=0.62)
    ax_b.set_xticks(np.arange(len(profile_vals)))
    ax_b.set_xticklabels(profiles["profile"], fontsize=6.5)
    ax_b.set_ylabel("Predicted failure probability")
    b_top = math.ceil(profile_vals.max() / 0.05) * 0.05
    ax_b.set_ylim(0, b_top)
    ax_b.set_yticks(np.arange(0, b_top + 0.001, 0.10))
    for i, v in enumerate(profile_vals):
        ax_b.text(i, v + b_top * 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=6.5)
    despine(ax_b)
    add_panel_label(ax_b, "b", x=-0.16, y=1.10)

    # c, average marginal effects.
    plot_ame = ame[ame["model"].eq("main_pathway_high_green_dhd_hot")].copy()
    order = ["green_water_mismatch", "antecedent_nocturnal_retention", "z_ventilation_obstruction_index"]
    labels = {
        "green_water_mismatch": "Green-water\nmismatch",
        "antecedent_nocturnal_retention": "Antecedent\nretention",
        "z_ventilation_obstruction_index": "Obstructed\nform",
    }
    plot_ame = plot_ame.set_index("variable").loc[order].reset_index()
    vals = plot_ame["average_marginal_effect_probability_points_per_1sd"].to_numpy()
    ax_c.bar(np.arange(len(vals)), vals, color=[GREEN_DARK, RED, BLUE], width=0.58)
    ax_c.axhline(0, color="black", linewidth=0.8)
    ax_c.set_xticks(np.arange(len(vals)))
    ax_c.set_xticklabels([labels[v] for v in order])
    ax_c.set_ylabel("Marginal effect\n(probability units per 1 s.d.)")
    ax_c.set_ylim(0, 0.08)
    ax_c.set_yticks(np.arange(0, 0.081, 0.02))
    despine(ax_c)
    add_panel_label(ax_c, "c", x=-0.12, y=1.10)

    # d, control-factor reset decomposition.
    label_map = {
        "water_mismatch_to_regional_p25": "Water\nmismatch",
        "retention_to_regional_p25": "Retention",
        "obstruction_to_regional_p25": "Obstructed\nform",
        "joint_water_retention_obstruction_to_regional_p25": "Joint",
    }
    res = resets[resets["reset"].isin(label_map)].copy()
    res["label"] = res["reset"].map(label_map)
    vals = res["represented_resident_8day_intervals"].to_numpy() / 1e9
    ax_d.bar(np.arange(len(vals)), vals, color=[GREEN_DARK, RED, BLUE, GOLD], width=0.58)
    ax_d.set_xticks(np.arange(len(vals)))
    ax_d.set_xticklabels(res["label"])
    ax_d.set_ylabel("Associated represented\nresident-8-day intervals (billion)")
    ax_d.set_ylim(0, 10)
    ax_d.set_yticks(np.arange(0, 10.01, 2))
    despine(ax_d)
    add_panel_label(ax_d, "d", x=-0.12, y=1.10)

    out = FIG_OUT / "figure_5_reliability_pathway"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG_OUT.mkdir(parents=True, exist_ok=True)

    terms = pd.read_csv(OUT / "green_refuge_pathway_model_terms.csv")
    perf = pd.read_csv(OUT / "green_refuge_pathway_model_performance.csv")
    ame = pd.read_csv(OUT / "green_refuge_pathway_average_marginal_effects.csv")
    validation = pd.read_csv(OUT / "green_refuge_pathway_validation.csv")
    calibration = pd.read_csv(OUT / "green_refuge_pathway_out_of_time_calibration_deciles.csv")
    resets = pd.read_csv(OUT / "green_refuge_pathway_counterfactual_resets.csv")
    surface = pd.read_csv(OUT / "green_refuge_pathway_response_surface.csv")
    profiles = pd.read_csv(OUT / "green_refuge_pathway_profile_predictions.csv")
    fig_path = make_pathway_figure(terms, ame, resets, validation, calibration, surface, profiles)

    print("Read green-refuge reliability-pathway source tables from", OUT)
    print("Updated figure:", fig_path)
    print("\nMain performance:")
    print(perf.to_string(index=False))
    print("\nAverage marginal effects:")
    print(ame.to_string(index=False))
    print("\nValidation:")
    print(validation.to_string(index=False))
    print("\nCounterfactual resets:")
    print(resets.to_string(index=False))


if __name__ == "__main__":
    main()
