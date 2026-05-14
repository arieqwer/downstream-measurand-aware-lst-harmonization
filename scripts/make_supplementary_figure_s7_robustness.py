from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FormatStrFormatter, MaxNLocator


REPO_ROOT = Path(__file__).resolve().parents[1]
EXT = REPO_ROOT / "data" / "processed" / "extended_outputs_local"
OUT = EXT / "70_reviewer_risk_robustness"
FIG_OUT = REPO_ROOT / "outputs" / "figures" / "supplementary"

PANEL = REPO_ROOT / "data" / "not_included" / "TRC_threshold_analysis_panel_anom_corrected.parquet"
FAILURE_PANEL = EXT / "23_true_night_green_refuge_failure" / "true_night_green_refuge_failure_panel.parquet"
CITY_INDEX = EXT / "25_true_night_reliability_index" / "true_night_reliability_city_index.csv"
MATCHED_PAIRS = EXT / "26_matched_high_low_veg_controls" / "high_low_veg_matched_pairs.csv"
RETENTION_FULLPERIOD = REPO_ROOT / "data" / "processed" / "metadata" / "city_retention_fullperiod_corrected.csv"
FULL_META = REPO_ROOT / "data" / "processed" / "metadata" / "ucdb_city_metadata_with_population.csv"

GREEN = "#276749"
OLIVE = "#a3a76d"
RED = "#c23b22"
BLUE = "#2b6cb0"
SLATE = "#4b5563"
GOLD = "#d4a017"


def ci_mean(x: pd.Series) -> tuple[float, float, float]:
    x = pd.to_numeric(x, errors="coerce").dropna()
    if len(x) == 0:
        return np.nan, np.nan, np.nan
    mean = float(x.mean())
    if len(x) < 2:
        return mean, np.nan, np.nan
    se = float(x.std(ddof=1) / math.sqrt(len(x)))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def ensure_dirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG_OUT.mkdir(parents=True, exist_ok=True)


def load_core_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    city = pd.read_csv(CITY_INDEX)
    pairs = pd.read_csv(MATCHED_PAIRS)
    retention = pd.read_csv(RETENTION_FULLPERIOD)
    full_meta = pd.read_csv(FULL_META)
    for df in [city, retention, full_meta]:
        df["uc_id"] = df["uc_id"].astype(str)
    pairs["high_uc_id"] = pairs["high_uc_id"].astype(str)
    pairs["low_uc_id"] = pairs["low_uc_id"].astype(str)
    return city, pairs, retention, full_meta


def build_sampling_qc(city: pd.DataFrame, retention: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "uc_id",
        "unit",
        "dT_night",
        "n_obs_night",
        "n_built_night",
        "n_veg_night",
        "rzsm_pct",
        "vpd_pct",
        "veg_group",
    ]
    panel = pd.read_parquet(PANEL, columns=cols)
    panel["uc_id"] = panel["uc_id"].astype(str)
    panel["valid_night_strict"] = (
        panel["dT_night"].notna()
        & panel["n_built_night"].ge(5)
        & panel["n_veg_night"].ge(5)
    )
    panel["state"] = np.select(
        [
            panel["rzsm_pct"].ge(70) & panel["vpd_pct"].le(30),
            panel["rzsm_pct"].le(20) & panel["vpd_pct"].ge(80),
        ],
        ["MLD", "DHD"],
        default="other",
    )

    unit_summary = (
        panel.groupby(["uc_id", "unit"], observed=True)
        .agg(
            n_intervals=("dT_night", "size"),
            valid_night_strict_frac=("valid_night_strict", "mean"),
            mean_n_obs_night=("n_obs_night", "mean"),
            mean_n_built_night=("n_built_night", "mean"),
            mean_n_veg_night=("n_veg_night", "mean"),
        )
        .reset_index()
    )
    unit_wide = unit_summary.pivot(index="uc_id", columns="unit")
    unit_wide.columns = [f"{a}_{b}" for a, b in unit_wide.columns]
    unit_wide = unit_wide.reset_index()

    state_summary = (
        panel[panel["state"].isin(["MLD", "DHD"])]
        .groupby(["uc_id", "unit", "state"], observed=True)
        .agg(
            mean_n_obs_night=("n_obs_night", "mean"),
            mean_n_built_night=("n_built_night", "mean"),
            mean_n_veg_night=("n_veg_night", "mean"),
            valid_night_strict_frac=("valid_night_strict", "mean"),
        )
        .reset_index()
    )
    state_wide = state_summary.pivot(index=["uc_id", "unit"], columns="state")
    state_wide.columns = [f"{a}_{b}" for a, b in state_wide.columns]
    state_wide = state_wide.reset_index()
    for col in [
        "mean_n_obs_night",
        "mean_n_built_night",
        "mean_n_veg_night",
        "valid_night_strict_frac",
    ]:
        state_wide[f"{col}_dhd_minus_mld"] = state_wide.get(f"{col}_DHD") - state_wide.get(f"{col}_MLD")
    state_delta = state_wide.pivot(index="uc_id", columns="unit")
    state_delta.columns = [f"{a}_{b}" for a, b in state_delta.columns]
    state_delta = state_delta.reset_index()

    qc = unit_wide.merge(state_delta, on="uc_id", how="left")
    qc = qc.merge(retention, on="uc_id", how="left")
    qc = qc.merge(city[["uc_id", "veg_group"]], on="uc_id", how="left")

    pixel_cols = [
        "mean_n_built_night_core",
        "mean_n_built_night_ring10_20",
        "mean_n_veg_night_core",
        "mean_n_veg_night_ring10_20",
    ]
    qc["min_pixel_support"] = qc[pixel_cols].min(axis=1)
    qc["min_fullperiod_night_valid"] = qc[
        ["night_valid_frac_core", "night_valid_frac_ring10_20"]
    ].min(axis=1)
    qc["ring_built_share_proxy"] = qc["mean_n_built_night_ring10_20"] / (
        qc["mean_n_built_night_ring10_20"] + qc["mean_n_veg_night_ring10_20"]
    )
    imbalance_cols = [
        "mean_n_obs_night_dhd_minus_mld_core",
        "mean_n_obs_night_dhd_minus_mld_ring10_20",
        "valid_night_strict_frac_dhd_minus_mld_core",
        "valid_night_strict_frac_dhd_minus_mld_ring10_20",
    ]
    qc["max_abs_sampling_imbalance"] = qc[imbalance_cols].abs().max(axis=1)

    retained = qc[qc["uc_id"].isin(city["uc_id"])]
    p10_support = retained["min_pixel_support"].quantile(0.10)
    p90_ring_built = retained["ring_built_share_proxy"].quantile(0.90)
    p90_imbalance = retained["max_abs_sampling_imbalance"].quantile(0.90)

    qc["pass_valid75"] = qc["min_fullperiod_night_valid"].ge(0.75)
    qc["pass_pixel_support_p10"] = qc["min_pixel_support"].ge(p10_support)
    qc["pass_low_ring_built_proxy"] = qc["ring_built_share_proxy"].le(p90_ring_built)
    qc["pass_low_sampling_imbalance"] = qc["max_abs_sampling_imbalance"].le(p90_imbalance)
    qc["pass_combined_artifact_screen"] = (
        qc["pass_valid75"]
        & qc["pass_pixel_support_p10"]
        & qc["pass_low_ring_built_proxy"]
        & qc["pass_low_sampling_imbalance"]
    )

    qc.to_csv(OUT / "reviewer_modis_sampling_qc_city_table.csv", index=False)

    group_state = (
        panel[panel["state"].isin(["MLD", "DHD"])]
        .groupby(["veg_group", "unit", "state"], observed=True)
        .agg(
            n_city_intervals=("uc_id", "size"),
            mean_n_obs_night=("n_obs_night", "mean"),
            mean_n_built_night=("n_built_night", "mean"),
            mean_n_veg_night=("n_veg_night", "mean"),
            valid_night_strict_frac=("valid_night_strict", "mean"),
        )
        .reset_index()
    )
    group_state.to_csv(OUT / "reviewer_modis_sampling_state_summary.csv", index=False)
    return qc


def matched_artifact_sensitivity(pairs: pd.DataFrame, qc: pd.DataFrame) -> pd.DataFrame:
    flags = [
        ("All matched pairs", None),
        ("Both cities night-valid fraction ≥0.75", "pass_valid75"),
        ("Both cities above 10th percentile pixel support", "pass_pixel_support_p10"),
        ("Exclude highest 10% ring built-share proxy", "pass_low_ring_built_proxy"),
        ("Exclude strongest 10% DHD-MLD sampling imbalance", "pass_low_sampling_imbalance"),
        ("Combined artifact screen", "pass_combined_artifact_screen"),
    ]
    qc_flags = qc.set_index("uc_id")[
        [
            "pass_valid75",
            "pass_pixel_support_p10",
            "pass_low_ring_built_proxy",
            "pass_low_sampling_imbalance",
            "pass_combined_artifact_screen",
        ]
    ]
    rows = []
    for label, flag in flags:
        if flag is None:
            mask = pd.Series(True, index=pairs.index)
        else:
            high = pairs["high_uc_id"].map(qc_flags[flag]).fillna(False)
            low = pairs["low_uc_id"].map(qc_flags[flag]).fillna(False)
            mask = high & low
        sub = pairs.loc[mask].copy()
        row = {"filter": label, "n_pairs": int(len(sub)), "share_pairs_retained": len(sub) / len(pairs)}
        for outcome in [
            "diff_compound_failure_loss_dhd_minus_mld",
            "diff_p_failure_given_hot_dhd",
            "diff_gradient_shift_dhd_minus_mld",
        ]:
            mean, low, high = ci_mean(sub[outcome])
            row[f"{outcome}_mean"] = mean
            row[f"{outcome}_ci95_low"] = low
            row[f"{outcome}_ci95_high"] = high
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "reviewer_modis_artifact_matched_sensitivity.csv", index=False)
    return out


def threshold_sensitivity() -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = [
        "uc_id",
        "veg_group",
        "year",
        "step8",
        "dhd",
        "anomalous_core_warmer",
        "population_2025",
        "t2m_true_night_c",
        "heat_true_night_t2m_local_p90",
        "heat_true_night_t2m_local_p95",
        "heat_true_night_t2m_ge25",
        "heat_true_night_t2m_ge28",
        "heat_true_night_wetbulb_local_p90",
    ]
    fp = pd.read_parquet(FAILURE_PANEL, columns=cols)
    fp["uc_id"] = fp["uc_id"].astype(str)
    fp["heat_t2m_ge26"] = fp["t2m_true_night_c"].ge(26)
    fp["heat_t2m_local_p90_ge25"] = fp["heat_true_night_t2m_local_p90"].astype(bool) & fp["t2m_true_night_c"].ge(25)
    fp["heat_t2m_local_p90_ge26"] = fp["heat_true_night_t2m_local_p90"].astype(bool) & fp["t2m_true_night_c"].ge(26)

    metrics = [
        ("Local 2m P90", "heat_true_night_t2m_local_p90"),
        ("Local 2m P95", "heat_true_night_t2m_local_p95"),
        ("Local 2m P90 + ≥25 °C", "heat_t2m_local_p90_ge25"),
        ("Local 2m P90 + ≥26 °C", "heat_t2m_local_p90_ge26"),
        ("Absolute ≥25 °C", "heat_true_night_t2m_ge25"),
        ("Absolute ≥26 °C", "heat_t2m_ge26"),
        ("Absolute ≥28 °C", "heat_true_night_t2m_ge28"),
        ("Wet-bulb local P90", "heat_true_night_wetbulb_local_p90"),
    ]

    rows = []
    exposure_rows = []
    for metric_label, flag_col in metrics:
        heat = fp[flag_col].fillna(False).astype(bool)
        failure = fp["dhd"].astype(bool) & heat & fp["anomalous_core_warmer"].astype(bool)
        dhd_hot = fp["dhd"].astype(bool) & heat
        tmp = fp[["uc_id", "veg_group", "year", "step8", "population_2025", "dhd"]].copy()
        tmp["heat"] = heat.to_numpy()
        tmp["dhd_hot"] = dhd_hot.to_numpy()
        tmp["failure"] = failure.to_numpy()
        for veg, sub in tmp.groupby("veg_group", observed=True):
            n_dhd = int(sub["dhd"].sum())
            n_hot = int(sub["dhd_hot"].sum())
            n_fail = int(sub["failure"].sum())
            rows.append(
                {
                    "metric": metric_label,
                    "veg_group": veg,
                    "n_dhd_intervals": n_dhd,
                    "n_dhd_hot_intervals": n_hot,
                    "n_failure_intervals": n_fail,
                    "share_failure_given_dhd_hot": n_fail / n_hot if n_hot else np.nan,
                    "failure_fraction_of_dhd": n_fail / n_dhd if n_dhd else np.nan,
                    "dhd_hot_fraction": n_hot / n_dhd if n_dhd else np.nan,
                }
            )
            recent = sub[sub["year"].between(2021, 2025)].copy()
            interval = (
                recent[recent["failure"]]
                .groupby(["year", "step8"], observed=True)["population_2025"]
                .sum()
                .reset_index(name="concurrent_population")
            )
            all_idx = pd.MultiIndex.from_product([range(2021, 2026), range(1, 47)], names=["year", "step8"]).to_frame(index=False)
            interval = all_idx.merge(interval, on=["year", "step8"], how="left").fillna({"concurrent_population": 0.0})
            city_year = (
                recent.groupby(["year", "uc_id"], observed=True)
                .agg(any_failure=("failure", "max"), population_2025=("population_2025", "first"))
                .reset_index()
            )
            annual_once = city_year[city_year["any_failure"].astype(bool)].groupby("year")["population_2025"].sum()
            exposure_rows.append(
                {
                    "metric": metric_label,
                    "veg_group": veg,
                    "mean_concurrent_2021_2025": interval["concurrent_population"].mean(),
                    "max_concurrent_2021_2025": interval["concurrent_population"].max(),
                    "mean_annual_atleast_once_2021_2025": annual_once.reindex(range(2021, 2026), fill_value=0.0).mean(),
                    "max_annual_atleast_once_2021_2025": annual_once.reindex(range(2021, 2026), fill_value=0.0).max(),
                }
            )

    summary = pd.DataFrame(rows)
    high = summary[summary["veg_group"].eq("high_veg")].set_index("metric")
    low = summary[summary["veg_group"].eq("low_veg")].set_index("metric")
    diffs = []
    for metric in high.index:
        diffs.append(
            {
                "metric": metric,
                "high_minus_low_failure_given_dhd_hot": high.loc[metric, "share_failure_given_dhd_hot"] - low.loc[metric, "share_failure_given_dhd_hot"],
                "high_minus_low_failure_fraction_of_dhd": high.loc[metric, "failure_fraction_of_dhd"] - low.loc[metric, "failure_fraction_of_dhd"],
                "high_minus_low_dhd_hot_fraction": high.loc[metric, "dhd_hot_fraction"] - low.loc[metric, "dhd_hot_fraction"],
            }
        )
    diff_df = pd.DataFrame(diffs)
    summary = summary.merge(diff_df, on="metric", how="left")
    exposure = pd.DataFrame(exposure_rows)
    summary.to_csv(OUT / "reviewer_threshold_sensitivity_summary.csv", index=False)
    exposure.to_csv(OUT / "reviewer_threshold_sensitivity_exposure.csv", index=False)
    return summary, exposure


def poststratified_burden(city: pd.DataFrame, full_meta: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    fp = pd.read_parquet(
        FAILURE_PANEL,
        columns=[
            "uc_id",
            "veg_group",
            "year",
            "step8",
            "population_2025",
            "true_green_refuge_failure_local_t2m_p90",
        ],
    )
    fp["uc_id"] = fp["uc_id"].astype(str)
    full = full_meta.copy()
    full["population_2025"] = pd.to_numeric(full["population_2025"], errors="coerce")
    full["pop_quintile"] = pd.qcut(full["population_2025"].rank(method="first"), 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
    full["stratum"] = full["un_sdg_reg"].fillna("Unknown") + " | " + full["wb_income"].fillna("Unknown") + " | " + full["pop_quintile"].astype(str)

    retained = city[["uc_id"]].merge(full[["uc_id", "stratum", "population_2025"]], on="uc_id", how="left")
    full_pop = full.groupby("stratum")["population_2025"].sum().rename("full_stratum_population")
    retained_pop = retained.groupby("stratum")["population_2025"].sum().rename("retained_stratum_population")
    weights = pd.concat([full_pop, retained_pop], axis=1).reset_index()
    weights["coverage"] = weights["retained_stratum_population"] / weights["full_stratum_population"]
    weights["poststrat_weight"] = weights["full_stratum_population"] / weights["retained_stratum_population"]
    weights["poststrat_weight"] = weights["poststrat_weight"].replace([np.inf, -np.inf], np.nan)
    weights["poststrat_weight_capped10"] = weights["poststrat_weight"].clip(upper=10)
    city_weights = full[["uc_id", "stratum"]].merge(weights[["stratum", "poststrat_weight", "poststrat_weight_capped10"]], on="stratum", how="left")

    fp = fp.merge(city_weights, on="uc_id", how="left")
    fp["current_population"] = fp["population_2025"]
    fp["poststrat_population"] = fp["population_2025"] * fp["poststrat_weight"]
    fp["poststrat_capped10_population"] = fp["population_2025"] * fp["poststrat_weight_capped10"]
    fp = fp[fp["veg_group"].eq("high_veg") & fp["year"].between(2021, 2025)].copy()
    fp["failure"] = fp["true_green_refuge_failure_local_t2m_p90"].astype(bool)

    schemes = [
        ("represented_panel", "current_population"),
        ("poststratified_to_full_ucdb", "poststrat_population"),
        ("poststratified_capped_weight_10", "poststrat_capped10_population"),
    ]
    rows = []
    for scheme, pop_col in schemes:
        interval = (
            fp[fp["failure"]]
            .groupby(["year", "step8"], observed=True)[pop_col]
            .sum()
            .reset_index(name="concurrent_population")
        )
        all_idx = pd.MultiIndex.from_product([range(2021, 2026), range(1, 47)], names=["year", "step8"]).to_frame(index=False)
        interval = all_idx.merge(interval, on=["year", "step8"], how="left").fillna({"concurrent_population": 0.0})
        city_year = (
            fp.groupby(["year", "uc_id"], observed=True)
            .agg(any_failure=("failure", "max"), pop=(pop_col, "first"))
            .reset_index()
        )
        annual_once = city_year[city_year["any_failure"].astype(bool)].groupby("year")["pop"].sum()
        rows.append(
            {
                "scheme": scheme,
                "mean_concurrent_2021_2025": interval["concurrent_population"].mean(),
                "max_concurrent_2021_2025": interval["concurrent_population"].max(),
                "mean_annual_atleast_once_2021_2025": annual_once.reindex(range(2021, 2026), fill_value=0.0).mean(),
                "max_annual_atleast_once_2021_2025": annual_once.reindex(range(2021, 2026), fill_value=0.0).max(),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "reviewer_poststratified_burden_summary.csv", index=False)

    weight_summary = pd.DataFrame(
        [
            {
                "n_full_cities": int(full["uc_id"].nunique()),
                "n_retained_cities": int(city["uc_id"].nunique()),
                "full_population": full["population_2025"].sum(),
                "retained_population": retained["population_2025"].sum(),
                "n_strata": int(weights.shape[0]),
                "n_strata_with_retained": int(weights["retained_stratum_population"].notna().sum()),
                "full_population_in_covered_strata": weights.loc[weights["retained_stratum_population"].notna(), "full_stratum_population"].sum(),
                "median_weight": weights["poststrat_weight"].median(),
                "p90_weight": weights["poststrat_weight"].quantile(0.90),
                "max_weight": weights["poststrat_weight"].max(),
            }
        ]
    )
    weights.to_csv(OUT / "reviewer_poststratification_stratum_weights.csv", index=False)
    weight_summary.to_csv(OUT / "reviewer_poststratification_weight_summary.csv", index=False)
    return out, weight_summary


def make_robustness_figure(
    artifact: pd.DataFrame,
    thresh: pd.DataFrame,
    thresh_exp: pd.DataFrame,
    post: pd.DataFrame,
) -> Path:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7,
            "axes.labelsize": 7.5,
            "xtick.labelsize": 6.6,
            "ytick.labelsize": 6.6,
            "legend.fontsize": 6.6,
            "axes.titlesize": 9,
            "figure.dpi": 150,
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(7.25, 6.6))
    ax = axes[0, 0]
    plot_art = artifact.copy()
    plot_art["short"] = [
        "All",
        "Night-valid\nfraction ≥0.75",
        "Pixel\nsupport",
        "Low ring\nbuilt proxy",
        "Low sampling\nimbalance",
        "Combined",
    ]
    y = np.arange(len(plot_art))[::-1]
    mean = plot_art["diff_compound_failure_loss_dhd_minus_mld_mean"]
    low = plot_art["diff_compound_failure_loss_dhd_minus_mld_ci95_low"]
    high = plot_art["diff_compound_failure_loss_dhd_minus_mld_ci95_high"]
    ax.axvline(0, color="black", lw=0.8, ls="--")
    ax.errorbar(mean, y, xerr=[mean - low, high - mean], fmt="o", color=GREEN, ecolor=GREEN, capsize=2.0, markersize=3.5)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_art["short"])
    ax.set_xlabel("Matched compound-loss effect")
    ax.xaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    ax.set_xlim(0, float(high.max()) * 1.08)
    ax.margins(x=0)
    ax.set_ylim(-0.5, len(plot_art) - 0.5)
    ax.text(-0.18, 1.08, "a", transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom")
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[0, 1]
    diff = thresh[["metric", "high_minus_low_failure_given_dhd_hot"]].drop_duplicates().copy()
    order = [
        "Local 2m P90",
        "Local 2m P95",
        "Local 2m P90 + ≥25 °C",
        "Local 2m P90 + ≥26 °C",
        "Absolute ≥25 °C",
        "Absolute ≥26 °C",
        "Absolute ≥28 °C",
        "Wet-bulb local P90",
    ]
    diff = diff.set_index("metric").loc[order].reset_index()
    ax.axhline(0, color="black", lw=0.8)
    ax.bar(np.arange(len(diff)), diff["high_minus_low_failure_given_dhd_hot"], color=[GREEN if v > 0 else RED for v in diff["high_minus_low_failure_given_dhd_hot"]])
    ax.set_xticks(np.arange(len(diff)))
    short_metric_labels = {
        "Local 2m P90": "2m P90",
        "Local 2m P95": "2m P95",
        "Local 2m P90 + ≥25 °C": "2m P90\n+ ≥25 °C",
        "Local 2m P90 + ≥26 °C": "2m P90\n+ ≥26 °C",
        "Absolute ≥25 °C": "Abs.\n≥25 °C",
        "Absolute ≥26 °C": "Abs.\n≥26 °C",
        "Absolute ≥28 °C": "Abs.\n≥28 °C",
        "Wet-bulb local P90": "Wet-bulb\nP90",
    }
    ax.set_xticklabels([short_metric_labels[m] for m in diff["metric"]], rotation=25, ha="right")
    ax.clear()
    yb = np.arange(len(diff))[::-1]
    ax.axvline(0, color="black", lw=0.8, ls="--")
    ax.barh(yb, diff["high_minus_low_failure_given_dhd_hot"], color=GREEN)
    ax.set_yticks(yb)
    ax.set_yticklabels([short_metric_labels[m].replace("\n", " ") for m in diff["metric"]])
    ax.set_xlabel("High-minus-low failure share")
    ax.xaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    ax.set_ylim(-0.5, len(diff) - 0.5)
    ax.text(-0.18, 1.08, "b", transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom")
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[1, 0]
    high_exp = thresh_exp[thresh_exp["veg_group"].eq("high_veg")].set_index("metric").loc[order].reset_index()
    yc = np.arange(len(high_exp))[::-1]
    ax.barh(yc, high_exp["max_concurrent_2021_2025"] / 1e6, color=BLUE)
    ax.set_yticks(yc)
    ax.set_yticklabels([short_metric_labels[m].replace("\n", " ") for m in high_exp["metric"]])
    ax.set_xlabel("Max concurrent exposure (millions)")
    ax.xaxis.set_major_locator(MaxNLocator(5))
    ax.set_ylim(-0.5, len(high_exp) - 0.5)
    ax.text(-0.18, 1.08, "c", transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom")
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[1, 1]
    scheme_labels = {
        "represented_panel": "Represented\npanel",
        "poststratified_to_full_ucdb": "Post-stratified",
        "poststratified_capped_weight_10": "Post-stratified\ncapped",
    }
    post = post.copy()
    post["label"] = post["scheme"].map(scheme_labels)
    x = np.arange(len(post))
    width = 0.36
    ax.bar(x - width / 2, post["max_concurrent_2021_2025"] / 1e6, width, color=GREEN, label="Max concurrent")
    ax.bar(x + width / 2, post["mean_annual_atleast_once_2021_2025"] / 1e6, width, color=GOLD, label="Mean annual exposed at least once")
    ax.set_xticks(x)
    ax.set_xticklabels(post["label"])
    ax.set_ylabel("Population (millions)")
    ax.legend(frameon=False, fontsize=5.8, loc="upper left", bbox_to_anchor=(0.02, 0.99), handlelength=1.0)
    ax.set_ylim(0, 1000)
    ax.set_yticks([0, 250, 500, 750, 1000])
    ax.text(-0.18, 1.08, "d", transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom")
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout(w_pad=2.4, h_pad=2.1)
    out = FIG_OUT / "supplementary_figure_s7_reviewer_risk_robustness.png"
    fig.savefig(out, dpi=400, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    ensure_dirs()
    artifact = pd.read_csv(OUT / "reviewer_modis_artifact_matched_sensitivity.csv")
    thresh = pd.read_csv(OUT / "reviewer_threshold_sensitivity_summary.csv")
    thresh_exp = pd.read_csv(OUT / "reviewer_threshold_sensitivity_exposure.csv")
    post = pd.read_csv(OUT / "reviewer_poststratified_burden_summary.csv")
    fig = make_robustness_figure(artifact, thresh, thresh_exp, post)

    print("Read reviewer-risk source tables from", OUT)
    print("Wrote robustness figure:", fig)
    print("\nArtifact matched sensitivity:")
    print(artifact.to_string(index=False))
    print("\nThreshold sensitivity high-minus-low:")
    print(thresh[["metric", "high_minus_low_failure_given_dhd_hot", "high_minus_low_failure_fraction_of_dhd"]].drop_duplicates().to_string(index=False))
    print("\nPost-stratified burden:")
    print(post.to_string(index=False))


if __name__ == "__main__":
    main()
