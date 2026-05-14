from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator, PercentFormatter

from nature_figure_style import add_panel_label, despine, save_figure, set_nature_style


REPO_ROOT = Path(__file__).resolve().parents[1]
METADATA = REPO_ROOT / "data" / "processed" / "metadata"
EXT = REPO_ROOT / "data" / "processed" / "extended_outputs_local"
OUT_ROOT = REPO_ROOT / "outputs"
MAIN_OUT = OUT_ROOT / "figures" / "main"
SUPP_OUT = OUT_ROOT / "figures" / "supplementary"

STATE_COLORS = {
    "moist_low_demand": "#2a9d8f",
    "DHD": "#e76f51",
    "extreme_DHD": "#9c1d35",
}
SURFACE_COLORS = {
    "built": "#d95f02",
    "veg": "#1b9e77",
    "relative": "#3b4252",
    "air": "#2b6cb0",
    "skin": "#56b4e9",
}


def short_region(name: str) -> str:
    mapping = {
        "Eastern and South-Eastern Asia": "East & SE Asia",
        "Central and Southern Asia": "Central & South Asia",
        "Latin America and the Caribbean": "Lat. America & Carib.",
        "Northern Africa and Western Asia": "N Africa & W Asia",
        "Sub-Saharan Africa": "Sub-Saharan Africa",
        "Northern America": "North America",
        "Australia and New Zealand": "Australia & NZ",
        "Europe": "Europe",
        "Oceania": "Oceania",
    }
    return mapping.get(name, name)


def stage_label(stage: str) -> str:
    mapping = {
        "all_11422_metadata": "All urban-centre metadata",
        "screened_2025": "2025 QC screened",
        "fullperiod_retained": "Full-period retained",
        "high_veg_main_subgroup": "High-vegetation main subgroup",
    }
    return mapping.get(stage, stage)


def short_stage_label(stage: str) -> str:
    mapping = {
        "all_11422_metadata": "All metadata",
        "screened_2025": "2025 screened",
        "fullperiod_retained": "Full-period retained",
        "high_veg_main_subgroup": "High-veg subgroup",
    }
    return mapping.get(stage, stage)


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def load_main_inputs() -> dict[str, pd.DataFrame]:
    return {
        "sample_counts": load_csv(EXT / "09_representativeness_airtemp_validation" / "sample_stage_counts.csv"),
        "day_state": load_csv(METADATA / "corrected_day_state_summary.csv"),
        "night_state": load_csv(METADATA / "corrected_night_state_summary.csv"),
        "air_state": load_csv(EXT / "09_representativeness_airtemp_validation" / "corrected_airtemp_state_summary.csv"),
        "annual_sync": load_csv(EXT / "06_sync_prevalence_null_robustness" / "corrected_core_highveg_annual_sync_summary.csv"),
        "sync_events": load_csv(EXT / "06_sync_prevalence_null_robustness" / "corrected_core_highveg_sync_event_annual_summary.csv"),
        "null_cmp": load_csv(EXT / "06_sync_prevalence_null_robustness" / "corrected_circular_shift_annual_comparison.csv"),
        "null_slopes": load_csv(EXT / "06_sync_prevalence_null_robustness" / "corrected_circular_shift_null_slope_summary.csv"),
        "threshold_sens": load_csv(EXT / "06_sync_prevalence_null_robustness" / "corrected_sync_threshold_sensitivity.csv"),
        "loo_sync": load_csv(EXT / "06_sync_prevalence_null_robustness" / "corrected_leave_one_region_out_sync_trend.csv"),
        "carry_terms": load_csv(EXT / "07_mechanistic_onset_carryover" / "carryover_panel_model_terms.csv"),
        "carry_fit": load_csv(EXT / "07_mechanistic_onset_carryover" / "carryover_panel_model_fit_summary.csv"),
        "carry_bins": load_csv(EXT / "07_mechanistic_onset_carryover" / "carryover_binned_descriptive.csv"),
        "onset_curve": load_csv(EXT / "07_mechanistic_onset_carryover" / "refined_onset_curve_summary.csv"),
        "attenuation": load_csv(EXT / "07_mechanistic_onset_carryover" / "refined_onset_attenuation_table.csv"),
        "penalties": load_csv(EXT / "08_heterogeneity_exposure" / "city_level_DHD_penalties.csv"),
        "exposure_city": load_csv(EXT / "08_heterogeneity_exposure" / "city_level_extreme_concurrence_exposure_q95.csv"),
        "concentration_summary": load_csv(EXT / "08_heterogeneity_exposure" / "city_level_exposure_concentration_summary_q95.csv"),
        "region_burden": load_csv(EXT / "08_heterogeneity_exposure" / "corrected_region_sync_burden_contribution_q95.csv"),
        "income_ratio": load_csv(EXT / "09_representativeness_airtemp_validation" / "retained_vs_all_by_income.csv"),
        "population_ratio": load_csv(EXT / "09_representativeness_airtemp_validation" / "retained_vs_all_population_quantile.csv"),
        "region_ratio": load_csv(EXT / "09_representativeness_airtemp_validation" / "retained_vs_all_by_region.csv"),
        "air_terms": load_csv(EXT / "09_representativeness_airtemp_validation" / "corrected_airtemp_state_contrast_model_terms.csv"),
        "burden_terms": load_csv(EXT / "09_representativeness_airtemp_validation" / "corrected_night_burden_plus_airtemp_model_terms.csv"),
    }


def prep_state(df: pd.DataFrame, order: list[str]) -> pd.DataFrame:
    out = df.copy()
    out["state"] = pd.Categorical(out["state"], categories=order, ordered=True)
    return out.sort_values("state")


def plot_sample_flow(ax: plt.Axes, counts: pd.DataFrame) -> None:
    order = ["all_11422_metadata", "screened_2025", "fullperiod_retained", "high_veg_main_subgroup"]
    data = counts.set_index("stage").loc[order].reset_index()
    data["label"] = data["stage"].map(stage_label)
    data["width"] = data["cities"] / data["cities"].max()
    y = np.arange(len(data))[::-1]
    colors = ["#0b3954", "#3d7a8c", "#7aa5b3", "#c7dfe8"]

    for idx, row in enumerate(data.itertuples(index=False)):
        yi = y[idx]
        ax.barh(yi, row.width, height=0.55, color=colors[idx], edgecolor="none")
        ax.text(-0.02, yi, row.label, ha="right", va="center")
        ax.text(min(1.05, row.width + 0.03), yi, f"{int(row.cities):,}", ha="left", va="center", fontweight="bold")
        if idx > 0:
            prev = data.iloc[idx - 1]["cities"]
            share = row.cities / prev
            ax.text(0.0, yi - 0.33, f"{share:.1%} of prior stage", ha="left", va="top", color="#495057", fontsize=7)

    ax.set_xlim(-0.38, 1.24)
    ax.set_ylim(-0.5, len(data) - 0.5)
    ax.axis("off")
    add_panel_label(ax, "a")


def plot_surface_state_panel(
    ax_abs: plt.Axes,
    ax_rel: plt.Axes,
    df: pd.DataFrame,
    built_col: str,
    veg_col: str,
    rel_col: str,
    panel_label: str,
    rel_ylabel: str,
    legend_bbox: tuple[float, float] | None = None,
    legend_ncol: int = 1,
    legend_fontsize: float | None = None,
) -> None:
    state_labels = ["Moist low\n demand", "DHD", "Extreme\n DHD"]
    x = np.arange(len(df))
    width = 0.28

    ax_abs.bar(x - width / 2, df[veg_col], width=width, color=SURFACE_COLORS["veg"], label="Vegetated surface")
    ax_abs.bar(x + width / 2, df[built_col], width=width, color=SURFACE_COLORS["built"], label="Built surface")
    ax_abs.axhline(0, color="black", linewidth=0.8)
    ax_abs.set_xticks(x)
    ax_abs.tick_params(axis="x", bottom=False, labelbottom=False)
    ax_abs.set_ylabel("Surface anomaly (°C)")
    abs_vals = np.r_[df[veg_col].to_numpy(dtype=float), df[built_col].to_numpy(dtype=float), 0.0]
    ax_abs.set_ylim(float(np.nanmin(abs_vals)), float(np.nanmax(abs_vals)))
    ax_abs.grid(False)

    ax_rel.plot(x, df[rel_col], color=SURFACE_COLORS["relative"], marker="o", linewidth=1.3, markersize=3.4)
    rel_vals = np.r_[df[rel_col].to_numpy(dtype=float), 0.0]
    ax_rel.set_ylim(float(np.nanmin(rel_vals)), float(np.nanmax(rel_vals)))
    ax_rel.axhline(0, color="black", linewidth=0.7)
    ax_rel.set_xticks(x)
    ax_rel.set_xticklabels(state_labels)
    ax_rel.set_ylabel(rel_ylabel, color=SURFACE_COLORS["relative"])
    ax_rel.tick_params(axis="y", colors=SURFACE_COLORS["relative"], labelsize=7.0)
    ax_rel.yaxis.set_major_locator(MaxNLocator(nbins=3))
    ax_rel.grid(False)

    handles = [
        Patch(facecolor=SURFACE_COLORS["veg"], label="Vegetated surface"),
        Patch(facecolor=SURFACE_COLORS["built"], label="Built surface"),
    ]
    legend_kwargs = {"loc": "upper left", "frameon": False, "ncol": legend_ncol, "handlelength": 1.8, "columnspacing": 1.2}
    if legend_fontsize is not None:
        legend_kwargs["fontsize"] = legend_fontsize
    if legend_bbox is not None:
        legend_kwargs["bbox_to_anchor"] = legend_bbox
    ax_abs.legend(handles=handles, **legend_kwargs)
    add_panel_label(ax_abs, panel_label)
    despine(ax_abs)
    despine(ax_rel)


def plot_air_state_panel(ax: plt.Axes, air: pd.DataFrame) -> None:
    state_labels = ["Moist low\n demand", "DHD", "Extreme\n DHD"]
    x = np.arange(len(air))
    width = 0.32
    ax.bar(x - width / 2, air["t2m_anom_mean"], width=width, color=SURFACE_COLORS["air"], label="2m air temperature")
    ax.bar(x + width / 2, air["skin_anom_mean"], width=width, color=SURFACE_COLORS["skin"], label="Skin temperature")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(state_labels)
    ax.set_ylabel("Temperature anomaly (°C)")
    vals = np.r_[air["t2m_anom_mean"].to_numpy(dtype=float), air["skin_anom_mean"].to_numpy(dtype=float), 0.0]
    ax.set_ylim(float(np.nanmin(vals)), float(np.nanmax(vals)))
    ax.grid(False)
    ax.legend(loc="upper left", frameon=False)
    add_panel_label(ax, "d")
    despine(ax)


def make_figure_1(data: dict[str, pd.DataFrame]) -> Path:
    order = ["moist_low_demand", "DHD", "extreme_DHD"]
    day = prep_state(data["day_state"], order)
    night = prep_state(data["night_state"], order)
    air = prep_state(data["air_state"], order)

    fig = plt.figure(figsize=(7.25, 6.45))
    outer = fig.add_gridspec(2, 1, hspace=0.5)
    top = outer[0].subgridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.58)
    bottom = outer[1].subgridspec(1, 2, width_ratios=[1.18, 0.82], wspace=0.78)
    b_stack = top[0, 1].subgridspec(2, 1, height_ratios=[3.0, 1.25], hspace=0.08)
    c_stack = bottom[0, 0].subgridspec(2, 1, height_ratios=[3.0, 1.25], hspace=0.08)
    ax_a = fig.add_subplot(top[0, 0])
    ax_b_abs = fig.add_subplot(b_stack[0, 0])
    ax_b_rel = fig.add_subplot(b_stack[1, 0], sharex=ax_b_abs)
    ax_c_abs = fig.add_subplot(c_stack[0, 0])
    ax_c_rel = fig.add_subplot(c_stack[1, 0], sharex=ax_c_abs)
    ax_d = fig.add_subplot(bottom[0, 1])

    plot_sample_flow(ax_a, data["sample_counts"])
    plot_surface_state_panel(ax_b_abs, ax_b_rel, day, "tb_day_anom_mean", "tv_day_anom_mean", "dT_day_anom_mean", "b", "Relative cooling\n(°C)", legend_bbox=(0.0, 1.02))
    plot_surface_state_panel(
        ax_c_abs,
        ax_c_rel,
        night,
        "tb_night_anom_mean",
        "tv_night_anom_mean",
        "dT_night_anom_mean",
        "c",
        "Relative cooling\n(°C)",
        legend_bbox=(0.0, 1.02),
        legend_fontsize=6.4,
    )
    plot_air_state_panel(ax_d, air)

    fig.subplots_adjust(top=0.97)
    out = MAIN_OUT / "figure_1_state_contrasts"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def plot_null_trend_panel(ax: plt.Axes, annual: pd.DataFrame, slope_tbl: pd.DataFrame, metric_key: str, null_key: str, low_key: str, high_key: str, panel_label: str, ylabel: str) -> None:
    x = annual["year"].to_numpy()
    ax.fill_between(x, annual[low_key], annual[high_key], color="#d4d8de", alpha=0.85, linewidth=0)
    ax.plot(x, annual[null_key], color="#7a7f87", linestyle="--", linewidth=1.1, label="Null mean")
    ax.plot(x, annual[metric_key], color="#0b5c88", linewidth=1.8, marker="o", markersize=2.6, label="Observed")
    ax.set_xlim(x.min() - 0.3, x.max() + 0.3)
    ax.set_xticks(np.arange(2004, 2026, 4))
    ax.set_ylabel(ylabel)
    vals = np.r_[
        annual[low_key].to_numpy(dtype=float),
        annual[high_key].to_numpy(dtype=float),
        annual[null_key].to_numpy(dtype=float),
        annual[metric_key].to_numpy(dtype=float),
    ]
    ax.set_ylim(float(np.nanmin(vals)), float(np.nanmax(vals)))
    ax.grid(False)
    row = slope_tbl.loc[slope_tbl["metric"] == metric_key].iloc[0]
    ax.text(0.98, 0.07, f"Empirical P = {row['empirical_p_one_sided']:.3f}", transform=ax.transAxes, ha="right", va="bottom", fontsize=7, color="#374151")
    add_panel_label(ax, panel_label)
    despine(ax)


def make_figure_2(data: dict[str, pd.DataFrame]) -> Path:
    fig = plt.figure(figsize=(7.25, 6.15))
    gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.28)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    annual = data["null_cmp"]
    slopes = data["null_slopes"].copy()
    slopes["metric"] = slopes["metric"].str.strip()

    plot_null_trend_panel(ax_a, annual, slopes, "mean_frac_compound_night", "null_mean_mean", "null_q025_mean", "null_q975_mean", "a", "Mean fraction of cities")
    plot_null_trend_panel(ax_b, annual, slopes, "p90_frac_compound_night", "null_mean_p90", "null_q025_p90", "null_q975_p90", "b", "P90 fraction of cities")
    plot_null_trend_panel(ax_c, annual, slopes, "max_frac_compound_night", "null_mean_max", "null_q025_max", "null_q975_max", "c", "Maximum fraction of cities")

    events = data["sync_events"]
    years = events["year"].to_numpy()
    ax_d.plot(years, events["n_sync_p90"], color="#0b5c88", marker="o", linewidth=1.7, markersize=2.8, label="P90 sync events")
    ax_d.plot(years, events["n_sync_p95"], color="#c03a2b", marker="o", linewidth=1.5, markersize=2.8, label="P95 sync events")
    for col, color in [("n_sync_p90", "#0b5c88"), ("n_sync_p95", "#c03a2b")]:
        coef = np.polyfit(years, events[col], 1)
        ax_d.plot(years, np.polyval(coef, years), color=color, linestyle="--", linewidth=1.0, alpha=0.9)
    ax_d.set_xlim(years.min() - 0.3, years.max() + 0.3)
    ax_d.set_xticks(np.arange(2004, 2026, 4))
    ax_d.set_ylabel("Number of sync events")
    ax_d.set_ylim(0, float(events[["n_sync_p90", "n_sync_p95"]].to_numpy(dtype=float).max()))
    ax_d.grid(False)
    ax_d.legend(loc="upper left", frameon=False)
    add_panel_label(ax_d, "d")
    despine(ax_d)

    legend_handles = [
        Line2D([0], [0], color="#0b5c88", linewidth=1.8, marker="o", markersize=2.8, label="Observed"),
        Line2D([0], [0], color="#7a7f87", linestyle="--", linewidth=1.1, label="Null mean"),
        Patch(facecolor="#d4d8de", edgecolor="none", label="Null 95% interval"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", frameon=False, ncol=3, bbox_to_anchor=(0.53, 0.995))
    fig.subplots_adjust(top=0.90)
    out = MAIN_OUT / "figure_2_extreme_concurrence"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_figure_3(data: dict[str, pd.DataFrame]) -> Path:
    fig = plt.figure(figsize=(7.25, 6.2))
    outer = fig.add_gridspec(2, 1, hspace=0.44)
    top = outer[0].subgridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.48)
    bottom = outer[1].subgridspec(1, 2, width_ratios=[1.18, 0.82], wspace=0.72)
    ax_a = fig.add_subplot(top[0, 0])
    ax_b = fig.add_subplot(top[0, 1])
    ax_c = fig.add_subplot(bottom[0, 0])
    ax_d = fig.add_subplot(bottom[0, 1])

    terms = data["carry_terms"]
    joint = terms[terms["model"] == "joint_same_plus_lag"].copy()
    term_order = [
        "dhd",
        "tb_day_anom",
        "dT_day_anom",
        "t2m_anom",
        "dhd_l1",
        "tb_day_anom_l1",
        "dT_day_anom_l1",
    ]
    label_map = {
        "dhd": "Same-interval DHD",
        "tb_day_anom": "Same-interval day built",
        "dT_day_anom": "Same-interval relative cooling",
        "t2m_anom": "Air-temperature anomaly",
        "dhd_l1": "Lagged DHD",
        "tb_day_anom_l1": "Lagged day built",
        "dT_day_anom_l1": "Lagged relative cooling",
    }
    color_map = {
        "dhd": "#9c1d35",
        "tb_day_anom": "#d95f02",
        "dT_day_anom": "#3b4252",
        "t2m_anom": "#2b6cb0",
        "dhd_l1": "#c77d92",
        "tb_day_anom_l1": "#f4a261",
        "dT_day_anom_l1": "#8d99ae",
    }
    joint["ci_low"] = joint["coef"] - 1.96 * joint["std_err"]
    joint["ci_high"] = joint["coef"] + 1.96 * joint["std_err"]
    joint["order"] = joint["term"].map({term: i for i, term in enumerate(term_order)})
    joint = joint[joint["term"].isin(term_order)].sort_values("order")
    y = np.arange(len(joint))[::-1]
    ax_a.axvline(0, color="black", linewidth=0.8, linestyle="--")
    for yi, row in zip(y, joint.itertuples(index=False)):
        ax_a.errorbar(row.coef, yi, xerr=[[row.coef - row.ci_low], [row.ci_high - row.coef]], fmt="o", color=color_map[row.term], ecolor=color_map[row.term], elinewidth=1.2, capsize=2.0, markersize=3.5)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels([label_map[t] for t in joint["term"]])
    ax_a.set_xlabel("Joint FE coefficient")
    add_panel_label(ax_a, "a")
    despine(ax_a)

    bins = data["carry_bins"].copy()
    for flag, color in [("non_DHD", "#5b7c99"), ("DHD", "#d95f02")]:
        sub = bins[bins["dhd_flag"] == flag].sort_values("mean_tb_day_anom")
        if len(sub) == 0:
            continue
        ax_b.plot(sub["mean_tb_day_anom"], sub["mean_tb_night_anom"], marker="o", linewidth=1.6, markersize=3.0, color=color, label=flag.replace("_", " "))
    ax_b.axhline(0, color="black", linewidth=0.8)
    ax_b.set_xlabel("Mean daytime built anomaly within bin (°C)")
    ax_b.set_ylabel("Mean nighttime built anomaly (°C)")
    ax_b.grid(False)
    ax_b.legend(loc="upper left", frameon=False)
    add_panel_label(ax_b, "b")
    despine(ax_b)

    curve = data["onset_curve"].copy()
    curve_map = {
        "tb_night_anom": ("Nighttime built anomaly", "#0b5c88"),
        "tb_day_anom": ("Daytime built anomaly", "#d95f02"),
        "t2m_anom": ("Air-temperature anomaly", "#2b6cb0"),
        "dT_day_anom": ("Relative daytime cooling", "#3b4252"),
    }
    for outcome, (label, color) in curve_map.items():
        sub = curve[curve["outcome"] == outcome].sort_values("event_time")
        if len(sub) == 0:
            continue
        alpha = 0.15 if outcome != "dT_day_anom" else 0.08
        ax_c.fill_between(sub["event_time"], sub["p05"], sub["p95"], color=color, alpha=alpha, linewidth=0)
        ax_c.plot(sub["event_time"], sub["mean_effect"], color=color, linewidth=1.6 if outcome != "dT_day_anom" else 1.2, marker="o", markersize=3.0, linestyle="--" if outcome == "dT_day_anom" else "-",
                  label=label)
    ax_c.axhline(0, color="black", linewidth=0.8)
    ax_c.axvline(0, color="black", linestyle="--", linewidth=0.8)
    ax_c.set_xticks([-2, -1, 0, 1, 2])
    ax_c.set_xlabel("Event time (8-day intervals)")
    ax_c.set_ylabel("Change vs pre-onset mean (°C)")
    ax_c.legend(
        loc="upper left",
        bbox_to_anchor=(0.0, 1.02),
        frameon=False,
        ncol=2,
        columnspacing=0.7,
        handlelength=1.4,
        fontsize=6.1,
    )
    add_panel_label(ax_c, "c")
    despine(ax_c)

    att = data["attenuation"].copy()
    order = ["night_only", "plus_rel_day", "plus_day_built", "plus_both"]
    label_map_att = {
        "night_only": "Night effect only",
        "plus_rel_day": "+ Relative cooling",
        "plus_day_built": "+ Day built warming",
        "plus_both": "+ Both mediators",
    }
    color_att = {
        "night_only": "#adb5bd",
        "plus_rel_day": "#6c757d",
        "plus_day_built": "#d95f02",
        "plus_both": "#9c1d35",
    }
    att["model"] = pd.Categorical(att["model"], categories=order, ordered=True)
    att = att.sort_values("model")
    y = np.arange(len(att))
    vals = att["attenuation_vs_baseline_pct"].fillna(0)
    ax_d.barh(y, vals, color=[color_att[m] for m in att["model"]], height=0.62)
    ax_d.set_yticks(y)
    ax_d.set_yticklabels([label_map_att[m] for m in att["model"]])
    ax_d.invert_yaxis()
    ax_d.set_xlabel("Attenuation of onset night effect (%)")
    for yi, val in zip(y, vals):
        ax_d.text(val + 1.2, yi, f"{val:.1f}%", va="center", ha="left", fontsize=7)
    ax_d.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax_d.grid(False)
    add_panel_label(ax_d, "d")
    despine(ax_d)

    fig.subplots_adjust(top=0.96)
    out = MAIN_OUT / "figure_3_mechanism_onset"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_figure_4(data: dict[str, pd.DataFrame]) -> Path:
    fig = plt.figure(figsize=(7.25, 6.2))
    outer = fig.add_gridspec(2, 1, hspace=0.48)
    top = outer[0].subgridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.72)
    bottom = outer[1].subgridspec(1, 2, width_ratios=[0.92, 1.08], wspace=0.82)
    ax_a = fig.add_subplot(top[0, 0])
    ax_b = fig.add_subplot(top[0, 1])
    ax_c = fig.add_subplot(bottom[0, 0])
    ax_d = fig.add_subplot(bottom[0, 1])

    exposure = data["exposure_city"].copy().sort_values("total_weighted_burden_q95", ascending=False).reset_index(drop=True)
    exposure = exposure[exposure["total_weighted_burden_q95"] > 0].copy()
    exposure["city_rank_share"] = (np.arange(len(exposure)) + 1) / len(exposure)
    exposure["cum_burden_share"] = exposure["total_weighted_burden_q95"].cumsum() / exposure["total_weighted_burden_q95"].sum()
    ax_a.plot(exposure["city_rank_share"], exposure["cum_burden_share"], color="#9c1d35", linewidth=2.0)
    ax_a.plot([0, 1], [0, 1], color="#9aa5b1", linestyle="--", linewidth=1.0)
    for pct in [0.01, 0.10]:
        row = data["concentration_summary"].loc[np.isclose(data["concentration_summary"]["top_city_share_cutoff"], pct)].iloc[0]
        ax_a.scatter(pct, row["burden_share"], color="#9c1d35", s=18, zorder=4)
        ax_a.text(pct + 0.02, row["burden_share"] - 0.04, f"Top {int(pct*100)}%: {row['burden_share']:.0%}", fontsize=7, color="#4a5568")
    ax_a.set_xlim(0, 1)
    ax_a.set_ylim(0, 1)
    ax_a.set_xlabel("Share of cities")
    ax_a.set_ylabel("Cumulative burden share")
    ax_a.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax_a.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax_a.grid(False)
    add_panel_label(ax_a, "a", x=-0.32, y=1.14)
    despine(ax_a)

    region = data["region_burden"].copy().sort_values("burden_share", ascending=True)
    y = np.arange(len(region))
    ax_b.hlines(y, region["population_share"], region["burden_share"], color="#b0b8c1", linewidth=1.2)
    ax_b.scatter(region["population_share"], y, facecolor="white", edgecolor="#0b5c88", s=26, label="Population share", zorder=3)
    ax_b.scatter(region["burden_share"], y, color="#9c1d35", s=26, label="Burden share", zorder=3)
    ax_b.set_yticks(y)
    ax_b.set_yticklabels([short_region(x) for x in region["un_sdg_reg"]])
    ax_b.set_xlabel("Share")
    ax_b.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax_b.set_ylim(-0.5, len(region) - 0.5)
    ax_b.legend(loc="lower right", frameon=False)
    ax_b.grid(False)
    add_panel_label(ax_b, "b", x=-0.32, y=1.14)
    despine(ax_b)

    penalties = data["penalties"].copy()
    heat_order = ["cooler", "middle", "hotter"]
    penalty_groups = [penalties.loc[penalties["baseline_heat_tertile"] == level, "tb_penalty_DHD_minus_MLD"].dropna().to_numpy() for level in heat_order]
    bp = ax_c.boxplot(penalty_groups, patch_artist=True, widths=0.55, showfliers=False)
    fill_colors = ["#7aa5b3", "#d9a441", "#e76f51"]
    for patch, color in zip(bp["boxes"], fill_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
        patch.set_edgecolor("#4a5568")
    for item in bp["medians"]:
        item.set_color("#1f2933")
        item.set_linewidth(1.3)
    ax_c.set_xticks([1, 2, 3])
    ax_c.set_xticklabels(["Cooler", "Middle", "Hotter"])
    ax_c.set_ylabel("Nighttime burden penalty vs moist state (°C)")
    finite_penalties = np.concatenate([g for g in penalty_groups if len(g)])
    ax_c.set_ylim(float(np.nanmin(finite_penalties)), float(np.nanmax(finite_penalties)))
    ax_c.grid(False)
    add_panel_label(ax_c, "c", x=-0.32, y=1.14)
    despine(ax_c)

    income = data["income_ratio"].copy()
    income = income[income["wb_income"].notna()].copy()
    income["label"] = income["wb_income"]
    income["group"] = "Income group"
    income_order = {
        "Low income": 0,
        "Lower Middle": 1,
        "Upper Middle": 2,
        "High income": 3,
    }
    income["order"] = income["wb_income"].map(income_order)
    pop = data["population_ratio"].copy()
    pop["label"] = pop["pop_quantile"].map(
        {
            "Q1": "Population Q1",
            "Q2": "Population Q2",
            "Q3": "Population Q3",
            "Q4": "Population Q4",
            "Q5": "Population Q5",
        }
    )
    pop["group"] = "Population size"
    pop["order"] = pop["pop_quantile"].map({"Q1": 4, "Q2": 5, "Q3": 6, "Q4": 7, "Q5": 8})
    ratio = pd.concat(
        [
            income[["label", "retained_to_all_share_ratio", "group", "order"]],
            pop[["label", "retained_to_all_share_ratio", "group", "order"]],
        ],
        ignore_index=True,
    )
    ratio["color"] = ratio["group"].map({"Income group": "#0b5c88", "Population size": "#d95f02"})
    ratio = ratio.sort_values("order", ascending=True)
    y = np.arange(len(ratio))[::-1]
    ax_d.axvline(1.0, color="black", linewidth=0.8, linestyle="--")
    ax_d.hlines(y, 0, ratio["retained_to_all_share_ratio"], color=ratio["color"], linewidth=1.4, alpha=0.65)
    ax_d.scatter(ratio["retained_to_all_share_ratio"], y, color=ratio["color"], s=24, zorder=3)
    ax_d.set_yticks(y)
    ax_d.set_yticklabels(ratio["label"])
    ax_d.set_xlabel("Retained share / all-city share")
    ax_d.set_ylim(-0.5, len(ratio) - 0.5)
    ax_d.grid(False)
    add_panel_label(ax_d, "d", x=-0.32, y=1.14)
    despine(ax_d)

    fig.subplots_adjust(top=0.97)
    out = MAIN_OUT / "figure_4_exposure_representativeness"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_supplementary_figure_s1(data: dict[str, pd.DataFrame]) -> Path:
    fig = plt.figure(figsize=(8.3, 3.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[0.82, 1.38], wspace=0.56)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])

    sens = data["threshold_sens"].copy().sort_values("event_quantile")
    labels = [f"P{int(q * 100)}" for q in sens["event_quantile"]]
    colors = ["#7aa5b3", "#0b5c88", "#9c1d35"]
    ax_a.bar(labels, sens["obs_slope"], color=colors, width=0.62)
    for idx, row in enumerate(sens.itertuples(index=False)):
        ptext = "P < 0.0001" if row.obs_pvalue < 1e-4 else f"P = {row.obs_pvalue:.4f}"
        label_y = min(float(row.obs_slope) + 0.012, 0.772)
        ax_a.text(idx, label_y, ptext, ha="center", va="bottom", fontsize=7, clip_on=False)
    ax_a.set_ylabel("Annual event-count slope")
    ax_a.set_ylim(0, 0.8)
    ax_a.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8])
    ax_a.grid(False)
    add_panel_label(ax_a, "a")
    despine(ax_a)

    loo = data["loo_sync"].copy().sort_values("coef_year")
    y = np.arange(len(loo))
    ax_b.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax_b.hlines(y, 0, loo["coef_year"], color="#7aa5b3", linewidth=1.2)
    ax_b.scatter(loo["coef_year"], y, color="#0b5c88", s=24)
    ax_b.set_yticks(y)
    ax_b.set_yticklabels([short_region(x) for x in loo["left_out_region"]])
    ax_b.tick_params(axis="y", labelsize=7.0)
    ax_b.set_xlabel("Leave-one-region-out trend")
    ax_b.xaxis.set_major_locator(MaxNLocator(nbins=4))
    ax_b.set_xlim(left=0)
    ax_b.margins(x=0)
    ax_b.set_ylim(-0.5, len(loo) - 0.5)
    ax_b.grid(False)
    add_panel_label(ax_b, "b")
    despine(ax_b)

    # Extra top breathing room prevents the panel-a annotation from being clipped
    # when the rendered image is embedded into Word.
    fig.subplots_adjust(top=0.88)
    out = SUPP_OUT / "supplementary_figure_s1_sync_robustness"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_supplementary_figure_s2(data: dict[str, pd.DataFrame]) -> Path:
    fig = plt.figure(figsize=(7.2, 6.0))
    outer = fig.add_gridspec(2, 1, hspace=0.52)
    top = outer[0].subgridspec(1, 2, wspace=0.42)
    bottom = outer[1].subgridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.52)
    ax_a = fig.add_subplot(top[0, 0])
    ax_b = fig.add_subplot(top[0, 1])
    ax_c = fig.add_subplot(bottom[0, 0])
    ax_d = fig.add_subplot(bottom[0, 1])

    region_ratio = data["region_ratio"].copy().sort_values("retained_to_all_share_ratio")
    y = np.arange(len(region_ratio))
    ax_a.axvline(1.0, color="black", linewidth=0.8, linestyle="--")
    ax_a.hlines(y, 0, region_ratio["retained_to_all_share_ratio"], color="#0b5c88", linewidth=1.2)
    ax_a.scatter(region_ratio["retained_to_all_share_ratio"], y, color="#0b5c88", s=20)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels([short_region(x) for x in region_ratio["un_sdg_reg"]])
    ax_a.set_xlabel("Retained share / all-city share")
    ax_a.set_xlim(0, float(region_ratio["retained_to_all_share_ratio"].max()) * 1.06)
    ax_a.margins(x=0)
    ax_a.set_ylim(-0.5, len(region_ratio) - 0.5)
    ax_a.grid(False)
    add_panel_label(ax_a, "a")
    despine(ax_a)

    air = data["air_state"].copy()
    order = ["moist_low_demand", "DHD", "extreme_DHD"]
    air = prep_state(air, order)
    x = np.arange(len(air))
    width = 0.25
    ax_b.bar(x - width, air["t2m_anom_mean"], width=width, color="#2b6cb0", label="2m air")
    ax_b.bar(x, air["skin_anom_mean"], width=width, color="#56b4e9", label="Skin")
    ax_b.bar(x + width, air["tb_night_anom_mean"], width=width, color="#d95f02", label="Night built")
    ax_b.axhline(0, color="black", linewidth=0.8)
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(["Moist", "DHD", "Extreme"])
    ax_b.set_ylabel("Mean anomaly (°C)")
    vals = np.r_[
        air["t2m_anom_mean"].to_numpy(dtype=float),
        air["skin_anom_mean"].to_numpy(dtype=float),
        air["tb_night_anom_mean"].to_numpy(dtype=float),
        0.0,
    ]
    ax_b.set_ylim(-1.5, 2.5)
    ax_b.set_yticks(np.arange(-1.5, 2.51, 0.5))
    ax_b.legend(loc="upper left", frameon=False)
    ax_b.grid(False)
    add_panel_label(ax_b, "b")
    despine(ax_b)

    coef_frames = []
    air_terms = data["air_terms"].copy()
    air_terms["display"] = air_terms["term"].map({"DHD_state": "DHD → air", "extreme_DHD_state": "Extreme DHD → air"})
    air_terms["group"] = "Air model"
    coef_frames.append(air_terms)
    burden_terms = data["burden_terms"].copy()
    burden_terms["display"] = burden_terms["term"].map(
        {
            "DHD_state": "DHD residual → night",
            "extreme_DHD_state": "Extreme residual → night",
            "t2m_anom": "Air → night burden",
        }
    )
    burden_terms["group"] = "Night-burden model"
    coef_frames.append(burden_terms)
    coef = pd.concat(coef_frames, ignore_index=True)
    coef["ci_low"] = coef["coef"] - 1.96 * coef["std_err"]
    coef["ci_high"] = coef["coef"] + 1.96 * coef["std_err"]
    order_terms = [
        "DHD → air",
        "Extreme DHD → air",
        "DHD residual → night",
        "Extreme residual → night",
        "Air → night burden",
    ]
    coef["display"] = pd.Categorical(coef["display"], categories=order_terms, ordered=True)
    coef = coef.sort_values("display")
    y = np.arange(len(coef))[::-1]
    colors = ["#2b6cb0", "#2b6cb0", "#9c1d35", "#9c1d35", "#0b5c88"]
    ax_c.axvline(0, color="black", linewidth=0.8, linestyle="--")
    for yi, row, color in zip(y, coef.itertuples(index=False), colors):
        ax_c.errorbar(row.coef, yi, xerr=[[row.coef - row.ci_low], [row.ci_high - row.coef]], fmt="o", color=color, ecolor=color, elinewidth=1.2, capsize=2.0, markersize=3.4)
    ax_c.set_yticks(y)
    ax_c.set_yticklabels([str(x) for x in coef["display"]])
    ax_c.set_xlabel("Coefficient")
    xmin = float(coef["ci_low"].min())
    xmax = float(coef["ci_high"].max())
    ax_c.set_xlim(min(-1.0, xmin * 1.12), max(1.0, xmax * 1.05))
    ax_c.set_ylim(-0.5, len(coef) - 0.5)
    add_panel_label(ax_c, "c")
    despine(ax_c)

    counts = data["sample_counts"].copy()
    counts["label"] = counts["stage"].map(short_stage_label)
    counts["share"] = counts["cities"] / counts.loc[counts["stage"] == "all_11422_metadata", "cities"].iloc[0]
    ax_d.plot(counts["share"], np.arange(len(counts))[::-1], marker="o", color="#0b5c88", linewidth=1.6)
    ax_d.set_yticks(np.arange(len(counts))[::-1])
    ax_d.set_yticklabels(counts["label"])
    ax_d.set_xlabel("Share of all metadata cities")
    ax_d.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax_d.set_xlim(0, 1.05)
    ax_d.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax_d.set_ylim(-0.5, len(counts) - 0.5)
    ax_d.grid(False)
    add_panel_label(ax_d, "d")
    despine(ax_d)

    fig.subplots_adjust(top=0.97)
    out = SUPP_OUT / "supplementary_figure_s2_validation_representativeness"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def write_manifest(paths: list[Path]) -> Path:
    rows = []
    for path in paths:
        rows.append({"figure_file": path.name, "absolute_path": str(path)})
    manifest = pd.DataFrame(rows)
    out = OUT_ROOT / "figure_manifest.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(out, index=False)
    return out


def main() -> None:
    set_nature_style()
    data = load_main_inputs()
    outputs = [
        make_supplementary_figure_s1(data),
        make_supplementary_figure_s2(data),
    ]
    manifest = write_manifest(outputs)
    print("Wrote figures:")
    for path in outputs:
        print(" -", path)
    print("Manifest:", manifest)


if __name__ == "__main__":
    main()
