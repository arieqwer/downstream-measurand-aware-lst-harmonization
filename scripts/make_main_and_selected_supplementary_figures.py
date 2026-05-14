from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Rectangle
from matplotlib.ticker import PercentFormatter

from nature_figure_style import add_panel_label, despine, save_figure, set_nature_style


REPO_ROOT = Path(__file__).resolve().parents[1]
EXT = REPO_ROOT / "data" / "processed" / "extended_outputs_local"
METADATA = REPO_ROOT / "data" / "processed" / "metadata"
OUT_ROOT = REPO_ROOT / "outputs"
MAIN_OUT = OUT_ROOT / "figures" / "main"
SUPP_OUT = OUT_ROOT / "figures" / "supplementary"

GREEN_DARK = "#276749"
GREEN_LIGHT = "#98c379"
RED = "#c23b22"
BLUE = "#2b6cb0"
SLATE = "#4b5563"
GOLD = "#d4a017"
TEAL = "#2a9d8f"
PURPLE = "#7c3aed"


def millions(x: float) -> float:
    return float(x) / 1e6


def billions(x: float) -> float:
    return float(x) / 1e9


def stage_label(stage: str) -> str:
    return {
        "all_11422_metadata": "All metadata",
        "screened_2025": "2025 screened",
        "fullperiod_retained": "Full-period retained",
        "high_veg_main_subgroup": "High-green support",
        "low_veg_comparator": "Low-green comparator",
    }.get(stage, stage)


def veg_group_label(veg: str, compact: bool = False) -> str:
    if compact:
        return {"high_veg": "High green", "low_veg": "Low green"}.get(veg, veg)
    return {"high_veg": "High-green support", "low_veg": "Low-green support"}.get(veg, veg)


def short_region(name: str) -> str:
    return {
        "Eastern and South-Eastern Asia": "East & SE Asia",
        "Central and Southern Asia": "Central & South Asia",
        "Latin America and the Caribbean": "Latin America & Carib.",
        "Northern Africa and Western Asia": "N Africa & W Asia",
        "Northern America": "North America",
        "Sub-Saharan Africa": "Sub-Saharan Africa",
        "Australia and New Zealand": "Australia & NZ",
        "Europe": "Europe",
    }.get(name, name)


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def add_box(ax, xy, width, height, text, fc, ec="#4b5563", fontsize=7.5):
    rect = FancyBboxPatch(xy, width, height, boxstyle="round,pad=0.02,rounding_size=0.03", facecolor=fc, edgecolor=ec, linewidth=0.8)
    ax.add_patch(rect)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, text, ha="center", va="center", fontsize=fontsize)


def add_arrow_box(ax, xy, width, height, text, fc, ec="#4b5563", fontsize=7.2):
    rect = FancyBboxPatch(xy, width, height, boxstyle="round,pad=0.02,rounding_size=0.02", facecolor=fc, edgecolor=ec, linewidth=0.8)
    ax.add_patch(rect)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, text, ha="center", va="center", fontsize=fontsize)


def main_inputs() -> dict[str, pd.DataFrame]:
    return {
        "sample_counts": load_csv(EXT / "09_representativeness_airtemp_validation" / "sample_stage_counts.csv"),
        "state_failure": load_csv(EXT / "23_true_night_green_refuge_failure" / "true_night_green_refuge_state_summary.csv"),
        "state_hot": load_csv(EXT / "21_true_nighttime_health_upgrade" / "true_nighttime_health_state_summary.csv"),
        "boundary": load_csv(EXT / "23_true_night_green_refuge_failure" / "true_night_green_refuge_failure_phase_boundary.csv"),
        "reliability_group": load_csv(EXT / "25_true_night_reliability_index" / "true_night_reliability_group_summary.csv"),
        "matched": load_csv(EXT / "26_matched_high_low_veg_controls" / "high_low_veg_matched_pair_effects.csv"),
        "fe_terms": load_csv(EXT / "27_formal_triple_interaction" / "formal_triple_interaction_model_terms.csv"),
        "exposure": load_csv(EXT / "23_true_night_green_refuge_failure" / "true_night_green_refuge_exposure_period_summary.csv"),
        "exposure_annual": load_csv(EXT / "23_true_night_green_refuge_failure" / "true_night_green_refuge_exposure_annual.csv"),
        "null": load_csv(EXT / "23_true_night_green_refuge_failure" / "true_night_green_refuge_circular_shift_null_slope_summary.csv"),
        "regional": load_csv(EXT / "23_true_night_green_refuge_failure" / "true_night_green_refuge_regional_exposure.csv"),
        "metric_compare": load_csv(EXT / "36_heat_stress_metric_upgrade" / "heat_stress_metric_failure_comparison.csv"),
        "metric_exposure": load_csv(EXT / "37_heat_danger_population_burden" / "heat_danger_population_exposure_period_summary.csv"),
        "traj": load_csv(EXT / "46_region_proxy_case_crossover" / "region_proxy_case_crossover_trajectory_summary.csv"),
        "regional_synoptic": load_csv(EXT / "45_region_case_crossover_mechanism" / "regional_synoptic_paired_tests.csv"),
        "counterfactual": load_csv(EXT / "50_counterfactual_excess_failure_attribution" / "counterfactual_attribution_summary.csv"),
        "climate_paired": load_csv(EXT / "49_climate_mode_stratification" / "regional_climate_mode_paired_tests.csv"),
        "climate_phase": load_csv(EXT / "49_climate_mode_stratification" / "regional_climate_mode_phase_enrichment.csv"),
        "survivor_perf": load_csv(EXT / "52_survivor_models_builtform" / "survivor_model_performance_builtform.csv"),
        "survivor_contrasts": load_csv(EXT / "52_survivor_models_builtform" / "survivor_quartile_feature_contrasts.csv"),
        "survivor_city_terms": load_csv(EXT / "52_survivor_models_builtform" / "survivor_city_model_terms_builtform.csv"),
        "conditional_profiles": load_csv(EXT / "54_conditional_refuge_interactions" / "conditional_refuge_predicted_profiles.csv"),
        "night_process": load_csv(EXT / "56_region_night_process_mechanism" / "regional_night_process_paired_tests.csv"),
        "synoptic_global": load_csv(EXT / "42_synoptic_matched_control_mechanism" / "synoptic_event_control_paired_tests.csv"),
        "archetypes": load_csv(EXT / "48_failure_regime_archetypes" / "failure_regime_archetype_totals.csv"),
        "proxy_perf": load_csv(EXT / "35_proxy_regime_models" / "proxy_regime_model_performance.csv"),
        "veg_breakdown": load_csv(EXT / "57_within_city_vegetation_breakdown" / "within_city_vegetation_breakdown_overall_tests.csv"),
        "veg_models": load_csv(EXT / "58_vegetation_breakdown_failure_models" / "vegetation_breakdown_model_terms.csv"),
        "onset_curves": load_csv(EXT / "59_true_night_failure_onset_event_study" / "failure_onset_curve_summary.csv"),
        "onset_attribution_fit": load_csv(EXT / "60_true_night_failure_onset_attribution" / "failure_onset_attribution_model_fit.csv"),
        "external_terms": load_csv(EXT / "64_external_process_validation_models" / "external_process_validation_city_model_terms.csv"),
        "external_scenarios": load_csv(EXT / "65_external_process_interaction_models" / "external_process_scenario_failure_rates.csv"),
        "water_onset": load_csv(EXT / "66_matched_water_support_onset_validation" / "matched_water_support_onset_tests.csv"),
        "water_onset_attr": load_csv(EXT / "66_matched_water_support_onset_validation" / "matched_water_support_attribution_terms.csv"),
        "water_obstruction": load_csv(EXT / "67_water_obstruction_onset_moderation" / "water_obstruction_onset_model_terms.csv"),
        "oneearth_veg_effects": load_csv(EXT / "68_oneearth_vegetation_definition_robustness" / "oneearth_vegetation_definition_matched_effects.csv"),
        "oneearth_veg_models": load_csv(EXT / "68_oneearth_vegetation_definition_robustness" / "oneearth_vegetation_continuous_model_terms.csv"),
        "oneearth_consequence": load_csv(EXT / "68_oneearth_vegetation_definition_robustness" / "oneearth_matched_effect_consequence.csv"),
        "oneearth_sync_nulls": load_csv(EXT / "69_oneearth_synchronization_nulls" / "oneearth_synchronization_additional_null_summary.csv"),
        "city_lookup": load_csv(METADATA / "ucdb_city_lookup_for_event_anatomy.csv"),
        "panel_city_base": load_csv(METADATA / "panel_city_base_corrected.csv"),
    }


def make_figure_1(data: dict[str, pd.DataFrame]) -> Path:
    fig = plt.figure(figsize=(7.25, 5.85))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.34, 1.0], hspace=0.56, wspace=0.38)
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])

    # a, Global retained-panel map. Dense city points create the global
    # footprint without relying on non-reproducible map tiles.
    panel = data["panel_city_base"].merge(data["city_lookup"][["uc_id", "lon", "lat"]], on="uc_id", how="left").dropna(subset=["lon", "lat"])
    colors = {"low_veg": "#a3a76d", "high_veg": GREEN_DARK}
    for veg in ["low_veg", "high_veg"]:
        s = panel[panel["veg_group"] == veg]
        ax_a.scatter(s["lon"], s["lat"], s=1.25, color=colors[veg], alpha=0.62, linewidths=0, label=veg_group_label(veg, compact=True))
    ax_a.set_xlim(-180, 180)
    ax_a.set_ylim(-60, 75)
    ax_a.set_xticks([-180, -120, -60, 0, 60, 120, 180])
    ax_a.set_yticks(np.arange(-60, 76, 15))
    ax_a.set_xlabel("Longitude")
    ax_a.set_ylabel("Latitude")
    ax_a.tick_params(length=2.2)
    ax_a.legend(frameon=False, loc="lower left", fontsize=6.5, handletextpad=0.3, markerscale=3.0)
    despine(ax_a)
    add_panel_label(ax_a, "a", x=-0.06, y=1.10)

    # b, Failure gate. Keep the logic compact and avoid making the panel
    # carry full methodological detail that is already in the text.
    ax_b.axis("off")
    ax_b.set_xlim(-0.04, 1.04)
    ax_b.set_ylim(0, 1)
    add_box(ax_b, (0.00, 0.60), 0.30, 0.22, "DHD\n(dry soil + high VPD)", "#f4cccc", fontsize=5.9)
    ax_b.text(0.345, 0.71, "+", ha="center", va="center", fontsize=12, fontweight="bold", color=SLATE)
    add_box(ax_b, (0.40, 0.60), 0.20, 0.22, "True-night\nheat", "#d9e8fb", fontsize=6.8)
    ax_b.text(0.655, 0.71, "+", ha="center", va="center", fontsize=12, fontweight="bold", color=SLATE)
    add_box(ax_b, (0.70, 0.60), 0.30, 0.22, "Anomalous\ncore warming", "#e6f4ea", fontsize=6.6)
    ax_b.add_patch(FancyArrowPatch((0.50, 0.58), (0.50, 0.40), arrowstyle="-|>", mutation_scale=12, linewidth=0.9, color=SLATE))
    add_box(ax_b, (0.18, 0.15), 0.64, 0.20, "Green-refuge failure", "#fee8c8", ec="#8d5524", fontsize=8.0)
    ax_b.text(0.50, 0.06, "Functional failure requires all three gates", ha="center", va="center", fontsize=6.7, color=SLATE)
    add_panel_label(ax_b, "b", x=-0.16, y=1.12)

    # c, Compact preview of the headline sign reversal.
    state = data["state_failure"].copy()
    high = state[state["veg_group"] == "high_veg"].set_index("state").loc[["MLD", "DHD", "extreme_DHD"]]
    x = np.arange(3)
    vals = high["mean_core_minus_ring_tb_night_anom"].to_numpy(dtype=float)
    bar_colors = ["#d8f3dc", "#f4cccc", "#d7301f"]
    ax_c.bar(x, vals, color=bar_colors, edgecolor="none", width=0.58)
    ax_c.axhline(0, color="black", lw=0.8)
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(["MLD", "DHD", "Extreme\nDHD"])
    ax_c.set_ylabel("High-green core-ring anomaly (°C)")
    ax_c.set_ylim(-0.15, 0.10)
    ax_c.set_yticks([-0.15, -0.10, -0.05, 0.00, 0.05, 0.10])
    despine(ax_c)
    add_panel_label(ax_c, "c", x=-0.16, y=1.12)

    out = MAIN_OUT / "figure_1_framework"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_figure_2(data: dict[str, pd.DataFrame]) -> Path:
    state_failure = data["state_failure"].copy()
    state_hot = data["state_hot"].copy()
    state = state_failure.merge(
        state_hot[["veg_group", "state", "frac_true_night_t2m_local_p90"]],
        on=["veg_group", "state"],
        how="left",
    )
    state["failure_rate_for_plot"] = state["frac_true_failure_local_t2m_p90"]
    state.loc[state["state"].eq("MLD"), "failure_rate_for_plot"] = np.nan

    order = ["MLD", "DHD", "extreme_DHD"]
    labels = ["MLD", "DHD", "Extreme DHD"]
    colors = {"high_veg": GREEN_DARK, "low_veg": "#a3a76d"}
    x = np.arange(len(order))
    width = 0.36

    fig, axes = plt.subplots(2, 2, figsize=(7.25, 6.0))

    ax = axes[0, 0]
    for i, veg in enumerate(["low_veg", "high_veg"]):
        sub = state[state["veg_group"].eq(veg)].set_index("state").reindex(order)
        ax.bar(x + (i - 0.5) * width, sub["mean_core_minus_ring_tb_night_anom"], width, color=colors[veg], label=veg_group_label(veg))
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Core-ring anomaly (°C)")
    vals_a = state.pivot_table(index="state", columns="veg_group", values="mean_core_minus_ring_tb_night_anom").reindex(order)
    ax.set_ylim(-0.15, 0.10)
    ax.set_yticks([-0.15, -0.10, -0.05, 0.00, 0.05, 0.10])
    despine(ax)
    add_panel_label(ax, "a")

    ax = axes[0, 1]
    for i, veg in enumerate(["low_veg", "high_veg"]):
        sub = state[state["veg_group"].eq(veg)].set_index("state").reindex(order)
        ax.bar(x + (i - 0.5) * width, sub["frac_anomalous_core_warmer"], width, color=colors[veg], label=veg_group_label(veg))
    ax.axhline(0.5, color="black", lw=0.8, ls="--")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Probability of anomalous core warming")
    vals_b = state.pivot_table(index="state", columns="veg_group", values="frac_anomalous_core_warmer").reindex(order)
    ax.set_ylim(0, 0.55)
    ax.set_yticks([0.00, 0.25, 0.50, 0.55])
    despine(ax)
    add_panel_label(ax, "b")

    ax = axes[1, 0]
    for i, veg in enumerate(["low_veg", "high_veg"]):
        sub = state[state["veg_group"].eq(veg)].set_index("state").reindex(order)
        ax.bar(x + (i - 0.5) * width, sub["frac_true_night_t2m_local_p90"], width, color=colors[veg], label=veg_group_label(veg))
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    vals_c = state.pivot_table(index="state", columns="veg_group", values="frac_true_night_t2m_local_p90").reindex(order)
    ax.set_ylim(0, 0.30)
    ax.set_yticks([0.00, 0.10, 0.20, 0.30])
    ax.set_ylabel("True-night local 2m P90 exceedance")
    despine(ax)
    add_panel_label(ax, "c")

    ax = axes[1, 1]
    failure_order = ["DHD", "extreme_DHD"]
    fx = np.arange(len(failure_order))
    for i, veg in enumerate(["low_veg", "high_veg"]):
        sub = state[state["veg_group"].eq(veg)].set_index("state").reindex(failure_order)
        ax.bar(fx + (i - 0.5) * width, sub["failure_rate_for_plot"], width, color=colors[veg], label=veg_group_label(veg))
    ax.set_xticks(fx)
    ax.set_xticklabels(["DHD", "Extreme DHD"])
    vals_d = state[state["state"].isin(failure_order)].pivot_table(index="state", columns="veg_group", values="failure_rate_for_plot").reindex(failure_order)
    ax.set_ylim(0, 0.14)
    ax.set_yticks([0.00, 0.05, 0.10, 0.14])
    ax.set_ylabel("Green-refuge failure rate")
    despine(ax)
    add_panel_label(ax, "d")

    handles = [
        Patch(facecolor=colors["low_veg"], edgecolor="none", label="Low-green support"),
        Patch(facecolor=colors["high_veg"], edgecolor="none", label="High-green support"),
    ]
    fig.legend(handles=handles, frameon=False, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.002), fontsize=8.6, handlelength=1.9, columnspacing=1.4)
    fig.tight_layout(w_pad=3.0, h_pad=2.6, rect=[0, 0.06, 1, 1])
    out = MAIN_OUT / "figure_2_true_night_state"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_figure_3(data: dict[str, pd.DataFrame]) -> Path:
    rel = data["reliability_group"].copy().set_index("veg_group")
    matched = data["matched"].copy()
    terms = data["fe_terms"].copy()
    veg_effects = data["oneearth_veg_effects"].copy()

    fig = plt.figure(figsize=(7.25, 6.1))
    gs = fig.add_gridspec(2, 2, hspace=0.48, wspace=0.76)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    metrics = [
        ("Hot-night\nreliability loss", "hot_reliability_loss_dhd_minus_mld_pop_weighted_mean"),
        ("Green-refuge\nfailure loss", "compound_failure_loss_dhd_minus_mld_pop_weighted_mean"),
        ("Core warming on\nDHD hot nights", "p_failure_given_hot_dhd_pop_weighted_mean"),
    ]
    y = np.arange(len(metrics))[::-1]
    observed = [rel.loc["high_veg", col] - rel.loc["low_veg", col] for _, col in metrics]
    ax_a.axvline(0, color="black", lw=0.8, ls="--")
    ax_a.barh(y, observed, height=0.46, color=GREEN_DARK, edgecolor="none")
    for yi, val in zip(y, observed):
        ax_a.text(val + 0.004, yi, f"+{val:.3f}", ha="left", va="center", fontsize=6.7, color=SLATE)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels([m[0] for m in metrics])
    ax_a.set_xlabel("Population-weighted high-minus-low probability")
    ax_a.set_xlim(0, max(observed) * 1.32)
    ax_a.margins(x=0)
    ax_a.set_ylim(-0.5, len(metrics) - 0.5)
    despine(ax_a)
    add_panel_label(ax_a, "a", x=-0.16, y=1.08)

    key_outcomes = ["hot_reliability_loss_dhd_minus_mld", "compound_failure_loss_dhd_minus_mld", "p_failure_given_hot_dhd"]
    label_map = {
        "hot_reliability_loss_dhd_minus_mld": "Hot-night\nreliability loss",
        "compound_failure_loss_dhd_minus_mld": "Green-refuge\nfailure loss",
        "p_failure_given_hot_dhd": "Core warming on\nDHD hot nights",
    }
    sub = matched[matched["outcome"].isin(key_outcomes)].copy()
    sub["label"] = sub["outcome"].map(label_map)
    sub = sub.set_index("outcome").loc[key_outcomes].reset_index()
    y = np.arange(len(sub))[::-1]
    ax_b.axvline(0, color="black", lw=0.8, ls="--")
    for yi, row in zip(y, sub.itertuples(index=False)):
        ax_b.errorbar(
            row.mean_high_minus_matched_low,
            yi,
            xerr=[[row.mean_high_minus_matched_low - row.ci95_low], [row.ci95_high - row.mean_high_minus_matched_low]],
            fmt="o",
            color=RED,
            ecolor=RED,
            elinewidth=1.2,
            capsize=2.0,
            markersize=3.6,
        )
    ax_b.set_yticks(y)
    ax_b.set_yticklabels(sub["label"])
    ax_b.set_xlabel("Matched high-minus-low probability")
    xmax_b = max(sub["ci95_high"].max() * 1.08, 0.01)
    ax_b.set_xlim(0, xmax_b)
    ax_b.margins(x=0)
    ax_b.set_ylim(-0.5, len(sub) - 0.5)
    despine(ax_b)
    add_panel_label(ax_b, "b", x=-0.34, y=1.20)

    pick = terms[
        (terms["model"] == "city_time_twfe_dhd_x_hot_x_highveg")
        & (terms["term"] == "dhd_high")
        & (terms["outcome"].isin(["core_minus_ring_tb_night_anom", "anomalous_core_warmer"]))
    ].copy()
    pick["label"] = pick["outcome"].map(
        {
            "core_minus_ring_tb_night_anom": "Core-ring anomaly\n(continuous °C)",
            "anomalous_core_warmer": "Core-warming probability\n(anomaly > 0)",
        }
    )
    pick = pick.set_index("outcome").loc[["core_minus_ring_tb_night_anom", "anomalous_core_warmer"]].reset_index()
    pick["ci_low"] = pick["coef"] - 1.96 * pick["std_err_cluster_city"]
    pick["ci_high"] = pick["coef"] + 1.96 * pick["std_err_cluster_city"]
    y = np.arange(len(pick))[::-1]
    for yi, row in zip(y, pick.itertuples(index=False)):
        ax_c.errorbar(row.coef, yi, xerr=[[row.coef - row.ci_low], [row.ci_high - row.coef]], fmt="o", color=RED, ecolor=RED, elinewidth=1.2, capsize=2.0, markersize=3.5)
    ax_c.set_yticks(y)
    ax_c.set_yticklabels(pick["label"])
    ax_c.set_xlabel("DHD × high-green FE coefficient")
    ax_c.set_xlim(0, float(pick["ci_high"].max()) * 1.05)
    ax_c.set_xticks([0.00, 0.02, 0.04, 0.06, 0.08])
    ax_c.set_ylim(-0.5, len(pick) - 0.5)
    despine(ax_c)
    ax_c.spines["left"].set_position(("data", 0.0))
    ax_c.spines["left"].set_visible(True)
    add_panel_label(ax_c, "c", x=-0.34, y=1.20)

    robust_labels = {
        "10-20 km ring vegetation support (original grouping variable)": "Ring support\n(10-20 km)",
        "core vegetation support": "Core support",
        "mean core-ring vegetation support": "Mean core-ring\nsupport",
        "10-20 km ring vegetation share": "Ring share\n(10-20 km)",
        "core vegetation share": "Core share",
        "mean core-ring vegetation share": "Mean core-ring\nshare",
    }
    sub = veg_effects[
        veg_effects["outcome"].eq("compound_failure_loss_dhd_minus_mld")
        & veg_effects["definition"].isin(robust_labels)
    ].copy()
    sub["label"] = sub["definition"].map(robust_labels)
    order = [
        "Ring support\n(10-20 km)",
        "Core support",
        "Mean core-ring\nsupport",
        "Ring share\n(10-20 km)",
        "Mean core-ring\nshare",
        "Core share",
    ]
    sub = sub.set_index("label").loc[order].reset_index()
    y = np.arange(len(sub))[::-1]
    ax_d.axvline(0, color="black", lw=0.8, ls="--")
    for yi, row in zip(y, sub.itertuples(index=False)):
        is_support = "support" in row.label
        color = GREEN_DARK if is_support else SLATE
        ax_d.errorbar(
            row.mean_higher_minus_lower,
            yi,
            xerr=[[row.mean_higher_minus_lower - row.ci95_low], [row.ci95_high - row.mean_higher_minus_lower]],
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=1.1,
            capsize=2.0,
            markersize=3.4,
        )
    ax_d.set_yticks(y)
    ax_d.set_yticklabels(sub["label"])
    ax_d.set_xlabel("Matched effect on failure loss")
    ax_d.set_ylim(-0.5, len(sub) - 0.5)
    despine(ax_d)
    add_panel_label(ax_d, "d")

    fig.subplots_adjust(top=0.97)
    out = MAIN_OUT / "figure_3_reliability_penalty"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_figure_4(data: dict[str, pd.DataFrame]) -> Path:
    exposure = data["exposure"].copy()
    exposure_annual = data["exposure_annual"].copy()
    metric_compare = data["metric_compare"].copy()
    sync_nulls = data["oneearth_sync_nulls"].copy()

    fig = plt.figure(figsize=(7.25, 5.7))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.08, 1.0], hspace=0.62, wspace=0.72)
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])

    sub = exposure_annual[exposure_annual["metric"] == "true_failure_local_t2m_p90"].copy()
    for veg, color in [("high_veg", GREEN_DARK), ("low_veg", "#a3a76d")]:
        s = sub[sub["veg_group"] == veg].sort_values("year")
        ax_a.plot(s["year"], [millions(v) for v in s["max_concurrent_exposed_population"]], linewidth=1.6, color=color, label=f"{veg_group_label(veg, compact=True)} max")
        ax_a.plot(s["year"], [millions(v) for v in s["mean_concurrent_exposed_population"]], linewidth=1.1, linestyle="--", color=color, alpha=0.9, label=f"{veg_group_label(veg, compact=True)} mean")
    ax_a.set_xlim(2003, 2025)
    ax_a.set_xticks([2003, 2008, 2013, 2018, 2023])
    high = sub[sub["veg_group"] == "high_veg"].sort_values("year")
    peak = high.loc[high["max_concurrent_exposed_population"].idxmax()]
    peak_m = millions(peak["max_concurrent_exposed_population"])
    ax_a.scatter([peak["year"]], [peak_m], s=18, color=GREEN_DARK, zorder=4)
    ax_a.annotate(
        f"{peak_m:.0f} million\nmaximum",
        xy=(peak["year"], peak_m),
        xytext=(peak["year"] - 2.2, 220),
        arrowprops=dict(arrowstyle="-", color=SLATE, lw=0.8),
        ha="right",
        va="center",
        fontsize=6.8,
        color=SLATE,
    )
    ax_a.set_ylim(0, 250)
    ax_a.set_yticks([0, 50, 100, 150, 200, 250])
    ax_a.set_ylabel("Concurrent exposure (millions)")
    ax_a.legend(frameon=False, fontsize=6.4, loc="upper center", bbox_to_anchor=(0.50, 1.16), ncol=4, handlelength=1.5, columnspacing=0.85)
    despine(ax_a)
    add_panel_label(ax_a, "a", x=-0.05, y=1.15)

    stat_order = [
        ("Region-block\nP90", "region-block circular shift", "p90_frac_event"),
        ("Region-block\nmaximum", "region-block circular shift", "max_frac_event"),
        ("Dry-hot timing\nP90", "DHD-hot-timing-preserving conditional failure null", "p90_frac_event"),
        ("Dry-hot timing\nmaximum", "DHD-hot-timing-preserving conditional failure null", "max_frac_event"),
    ]
    null_rows = []
    for label, null_name, stat in stat_order:
        row = sync_nulls[(sync_nulls["null_name"] == null_name) & (sync_nulls["statistic"] == stat)].iloc[0]
        null_rows.append({"label": label, **row.to_dict()})
    null_df = pd.DataFrame(null_rows)
    y = np.arange(len(null_df))[::-1]
    for yi, row in zip(y, null_df.itertuples(index=False)):
        lo = 100.0 * row.null_q025_slope
        hi = 100.0 * row.null_q975_slope
        obs = 100.0 * row.obs_slope
        ax_b.plot([lo, hi], [yi, yi], color="#9ca3af", lw=2.0, solid_capstyle="round")
        ax_b.plot(obs, yi, "o", color=RED, markersize=3.8)
        ptxt = "P < 0.01" if row.empirical_p_one_sided < 0.01 else f"P = {row.empirical_p_one_sided:.2f}"
        ax_b.text(max(hi, obs) + 0.006, yi, ptxt, va="center", ha="left", fontsize=6.0, color=SLATE)
    ax_b.set_yticks(y)
    ax_b.set_yticklabels(null_df["label"])
    ax_b.set_xlabel("Annual trend vs timing null\n(percentage points per year)")
    ax_b.set_xlim(0.08, 0.285)
    ax_b.set_xticks([0.10, 0.15, 0.20, 0.25])
    ax_b.set_ylim(-0.5, len(null_df) - 0.5)
    despine(ax_b)
    add_panel_label(ax_b, "b", x=-0.34, y=1.20)

    key_metrics = ["t2m_local_p90", "wetbulb_local_p90", "humidex_local_p90", "heat_index_local_p90"]
    label_map = {
        "t2m_local_p90": "2m P90",
        "wetbulb_local_p90": "wet-bulb P90",
        "humidex_local_p90": "Humidex P90",
        "heat_index_local_p90": "Heat Index P90",
    }
    sub = metric_compare[metric_compare["metric"].isin(key_metrics)].copy()
    sub["label"] = sub["metric"].map(label_map)
    x = np.arange(len(key_metrics))
    width = 0.34
    for i, veg in enumerate(["low_veg", "high_veg"]):
        s = sub[sub["veg_group"] == veg].set_index("metric").loc[key_metrics].reset_index()
        ax_c.bar(x + (i - 0.5) * width, s["share_dhd_hot_with_refuge_failure"], width, color=GREEN_DARK if veg == "high_veg" else "#a3a76d", label=veg_group_label(veg, compact=True))
    ax_c.set_xticks(x)
    ax_c.set_xticklabels([label_map[m] for m in key_metrics], rotation=18, ha="right")
    ax_c.set_ylabel("Share of DHD hot intervals\nwith green-refuge failure")
    ax_c.set_ylim(0, 0.6)
    ax_c.set_yticks([0.0, 0.2, 0.4, 0.6])
    ax_c.legend(frameon=False, loc="upper left", fontsize=6.2, handlelength=1.2)
    despine(ax_c)
    add_panel_label(ax_c, "c", x=-0.30, y=1.20)

    fig.subplots_adjust(top=0.97)
    out = MAIN_OUT / "figure_4_synchronization_exposure"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_figure_5(data: dict[str, pd.DataFrame]) -> Path:
    traj = data["traj"].copy()
    syn = data["regional_synoptic"].copy()
    cf = data["counterfactual"].copy()

    fig = plt.figure(figsize=(7.25, 6.45))
    gs = fig.add_gridspec(2, 2, hspace=0.68, wspace=0.58)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    lag_order = ["lag4", "lag2", "lag1", "lag0"]
    x = np.arange(len(lag_order))
    metric_specs = [
        ("VPD anomaly", lambda s: s),
        ("root-zone soil moisture anomaly", lambda s: -s),
        ("true-night 2m temperature anomaly", lambda s: s),
        ("core-ring anomaly", lambda s: s),
    ]
    color_map = {
        "VPD anomaly": RED,
        "root-zone soil moisture anomaly": GOLD,
        "true-night 2m temperature anomaly": BLUE,
        "core-ring anomaly": GREEN_DARK,
    }
    trajectory_values: dict[str, list[float]] = {}
    for ax, region, label in [(ax_a, "Europe", "a"), (ax_b, "Eastern and South-Eastern Asia", "b")]:
        sub = traj[traj["region"] == region].copy()
        plotted_vals = []
        for metric, transform in metric_specs:
            row = sub[sub["metric"] == metric].iloc[0]
            vals = np.array([row[f"{lag}_mean_event_minus_control"] for lag in lag_order], dtype=float)
            vals = transform(vals)
            scale = np.nanmax(np.abs(vals)) or 1.0
            norm = vals / scale
            plotted_vals.extend(norm.tolist())
            ax.plot(
                x,
                norm,
                marker="o",
                linewidth=1.6,
                markersize=3.0,
                color=color_map[metric],
                label=metric.replace("root-zone ", "").replace(" anomaly", ""),
                clip_on=False,
            )
        trajectory_values[region] = plotted_vals
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(["-4", "-2", "-1", "0"])
        ax.set_xlabel("Lag (8-day intervals)")
        ax.set_ylabel("Normalized event-control difference")
        # Keep exact axis limits while allowing markers on the boundary to
        # render fully outside the clipped data area.
        if label == "a":
            ax.set_ylim(-0.4, 1.0)
            ax.set_yticks(np.arange(-0.4, 1.0001, 0.2))
        else:
            ax.set_ylim(0.0, 1.0)
            ax.set_yticks(np.arange(0.0, 1.0001, 0.2))
        despine(ax)
        add_panel_label(ax, label)

    trajectory_handles = [
        Line2D([0], [0], color=color_map["VPD anomaly"], lw=1.6, marker="o", markersize=3, label="VPD"),
        Line2D([0], [0], color=color_map["root-zone soil moisture anomaly"], lw=1.6, marker="o", markersize=3, label="Soil drying"),
        Line2D([0], [0], color=color_map["true-night 2m temperature anomaly"], lw=1.6, marker="o", markersize=3, label="True-night 2m"),
        Line2D([0], [0], color=color_map["core-ring anomaly"], lw=1.6, marker="o", markersize=3, label="Core-ring"),
    ]
    fig.legend(handles=trajectory_handles, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.575), ncol=4, fontsize=7.0, columnspacing=1.0, handlelength=1.7)

    effect_specs = [
        ("z500_gpm", "Z500"),
        ("t850_c", "T850"),
        ("omega500_pa_s", "Omega500"),
        ("swvl_mean_m3_m3", "Soil drying"),
        ("tp_interval_mm", "Precip deficit"),
    ]
    plot_rows = []
    for region in ["Europe", "Eastern and South-Eastern Asia"]:
        sub = syn[syn["region"] == region].copy()
        for metric, label in effect_specs:
            row = sub[sub["metric"] == metric].iloc[0]
            signed = row["mean_event_minus_control"]
            if metric in {"swvl_mean_m3_m3", "tp_interval_mm"}:
                signed = -signed
            effect = signed / row["std_event_minus_control"] if row["std_event_minus_control"] not in (0, np.nan) else np.nan
            plot_rows.append({"region": region, "label": label, "effect_size": effect})
    eff = pd.DataFrame(plot_rows)
    order = ["Z500", "T850", "Omega500", "Soil drying", "Precip deficit"]
    y = np.arange(len(order))[::-1]
    width = 0.34
    for i, region in enumerate(["Europe", "Eastern and South-Eastern Asia"]):
        s = eff[eff["region"] == region].set_index("label").loc[order].reset_index()
        ax_c.barh(y + (i - 0.5) * width, s["effect_size"], height=width, color=RED if region == "Europe" else BLUE, label=short_region(region))
    ax_c.axvline(0, color="black", lw=0.8, ls="--")
    ax_c.set_yticks(y)
    ax_c.set_yticklabels(order)
    ax_c.set_xlabel("Standardized paired contrast")
    xmin_c = min(-0.15, float(eff["effect_size"].min()) * 1.20)
    xmax_c = max(0.15, float(eff["effect_size"].max()) * 1.12)
    ax_c.set_xlim(xmin_c, xmax_c)
    ax_c.set_xticks([round(xmin_c, 2), 0.0, 0.5, 1.0])
    ax_c.set_ylim(-0.5, len(order) - 0.5)
    despine(ax_c)
    add_panel_label(ax_c, "c")

    keep = ["reset_soil_memory", "reset_hotter_true_night", "reset_all_three"]
    label_map = {
        "reset_soil_memory": "Reset soil\nmemory",
        "reset_hotter_true_night": "Reset hot-night\nair",
        "reset_all_three": "Reset all\nthree",
    }
    sub = cf[cf["scenario"].isin(keep)].copy()
    x = np.arange(len(keep))
    width = 0.34
    for i, region in enumerate(["Europe", "Eastern and South-Eastern Asia"]):
        s = sub[sub["region"] == region].set_index("scenario").loc[keep].reset_index()
        vals = 100.0 * s["attributable_share_of_predicted_excess"].to_numpy(dtype=float)
        lo = vals - 100.0 * s["share_q05"].to_numpy(dtype=float)
        hi = 100.0 * s["share_q95"].to_numpy(dtype=float) - vals
        ax_d.bar(x + (i - 0.5) * width, vals, width, color=RED if region == "Europe" else BLUE, alpha=0.92, label=short_region(region))
        ax_d.errorbar(x + (i - 0.5) * width, vals, yerr=[lo, hi], fmt="none", ecolor="black", elinewidth=0.8, capsize=2.0)
    ax_d.axhline(0, color="black", lw=0.8)
    ax_d.set_xticks(x)
    ax_d.set_xticklabels([label_map[k] for k in keep], rotation=0, ha="center")
    ax_d.set_ylabel("Modeled share of predicted excess failure (%)")
    ax_d.set_ylim(-20, 50)
    ax_d.set_yticks([-20, -10, 0, 10, 20, 30, 40, 50])
    despine(ax_d)
    add_panel_label(ax_d, "d")

    region_handles = [
        Patch(facecolor=RED, edgecolor="none", label="Europe"),
        Patch(facecolor=BLUE, edgecolor="none", label="East & SE Asia"),
    ]
    fig.legend(handles=region_handles, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.035), ncol=2, fontsize=7.2)

    fig.subplots_adjust(top=0.96, bottom=0.15)
    out = MAIN_OUT / "figure_5_regional_mechanism"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_figure_6(data: dict[str, pd.DataFrame]) -> Path:
    onset = data["onset_curves"].copy()
    fit = data["onset_attribution_fit"].copy()
    ext = data["external_terms"].copy()
    scenarios = data["external_scenarios"].copy()
    water = data["water_onset"].copy()

    fig = plt.figure(figsize=(7.25, 6.25))
    gs = fig.add_gridspec(2, 2, hspace=0.52, wspace=0.72)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    curve_metrics = [
        ("core_tv_night_anom", "Core veg.", GREEN_DARK),
        ("core_minus_ring_tv_night_anom", "Core-ring veg.", TEAL),
        ("core_minus_ring_tb_night_anom", "Core-ring built", RED),
        ("t2m_true_night_c", "True-night 2m", BLUE),
    ]
    curve_values = []
    for metric, label, color in curve_metrics:
        sub = onset[onset["outcome"] == metric].sort_values("event_time")
        curve_values.extend(sub["mean_effect"].to_numpy(dtype=float).tolist())
        ax_a.plot(sub["event_time"], sub["mean_effect"], marker="o", linewidth=1.5, markersize=3.2, color=color, label=label)
    ax_a.axhline(0, color="black", linewidth=0.8)
    ax_a.axvline(0, color="#9ca3af", linewidth=0.8, linestyle="--")
    ax_a.set_xticks([-2, -1, 0, 1, 2])
    ax_a.set_xlabel("Failure-onset time (8-day intervals)")
    ax_a.set_ylabel("Matched onset change (°C)")
    ax_a.set_ylim(min(-0.5, min(curve_values)), max(curve_values))
    ax_a.set_yticks([-0.5, 0, 0.5, 1.0, 1.5, 2.0])
    ax_a.legend(frameon=False, fontsize=5.8, loc="upper left", bbox_to_anchor=(0.56, 1.06), handlelength=1.6)
    despine(ax_a)
    add_panel_label(ax_a, "a")

    model_order = ["air_only", "veg_night_only", "air_plus_veg_night", "full_surface_model"]
    label_map = {
        "air_only": "Air only",
        "veg_night_only": "Vegetation",
        "air_plus_veg_night": "Air + vegetation",
        "full_surface_model": "Full surface",
    }
    sub = fit[fit["model"].isin(model_order)].set_index("model").loc[model_order].reset_index()
    bars = ax_b.bar(np.arange(len(sub)), sub["r_squared"], color=[BLUE, GREEN_DARK, TEAL, RED])
    ax_b.set_xticks(np.arange(len(sub)))
    ax_b.set_xticklabels([label_map[m] for m in sub["model"]], rotation=20, ha="right")
    ax_b.set_ylabel("Onset decomposition model R²")
    ax_b.set_ylim(0, 0.7)
    ax_b.set_yticks(np.arange(0, 0.71, 0.1))
    for bar, value in zip(bars, sub["r_squared"]):
        y_text = value if value > 0 else 0.012
        ax_b.text(
            bar.get_x() + bar.get_width() / 2,
            y_text,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=6.2,
            color=SLATE,
            clip_on=False,
        )
    despine(ax_b)
    add_panel_label(ax_b, "b")

    term_specs = [
        ("z_mean_water_support_ratio", "Water support", True),
        ("z_ahe_night_wm2", "Anthropogenic heat", False),
        ("z_ventilation_obstruction_index", "Obstructed form", False),
    ]
    full = ext[ext["model"] == "full_external_process"].copy()
    rows = []
    for term, label, invert in term_specs:
        row = full[full["term"] == term].iloc[0]
        coef = -row["coef_probability_points"] if invert else row["coef_probability_points"]
        se = row["std_err_hc3"]
        rows.append({"label": label, "coef": coef, "ci_low": coef - 1.96 * se, "ci_high": coef + 1.96 * se})
    coef_df = pd.DataFrame(rows)
    y = np.arange(len(coef_df))[::-1]
    ax_c.axvline(0, color="black", linewidth=0.8, linestyle="--")
    for yi, row, color in zip(y, coef_df.itertuples(index=False), [GREEN_DARK, PURPLE, RED]):
        ax_c.errorbar(row.coef, yi, xerr=[[row.coef - row.ci_low], [row.ci_high - row.coef]], fmt="o", color=color, ecolor=color, capsize=2, markersize=3.8)
    ax_c.set_yticks(y)
    ax_c.set_yticklabels(coef_df["label"])
    ax_c.set_xlabel("Effect on failure probability\n(per 1 s.d.; water sign reversed)")
    ax_c.set_xlim(-0.02, 0.12)
    ax_c.set_xticks([-0.02, 0.00, 0.05, 0.10, 0.12])
    ax_c.set_ylim(-0.5, len(coef_df) - 0.5)
    despine(ax_c)
    add_panel_label(ax_c, "c")

    scen = scenarios.copy()
    scen["label"] = scen.apply(
        lambda r: ("Low water\n" if r["low_water_support"] else "High water\n")
        + ("high obstruction" if r["high_ventilation_obstruction"] else "low obstruction"),
        axis=1,
    )
    order = [
        "High water\nlow obstruction",
        "High water\nhigh obstruction",
        "Low water\nlow obstruction",
        "Low water\nhigh obstruction",
    ]
    scen = scen.set_index("label").loc[order].reset_index()
    x_d = np.arange(len(scen)) * 1.70
    ax_d.bar(x_d, scen["mean_p_failure"], width=0.62, color=[GREEN_LIGHT, "#8cbf88", GOLD, RED])
    ax_d.set_xticks(x_d)
    ax_d.set_xticklabels(scen["label"], rotation=20, ha="right")
    ax_d.set_ylabel("Mean failure probability")
    ax_d.set_ylim(0, 0.6)
    ax_d.set_yticks(np.arange(0, 0.61, 0.1))
    despine(ax_d)
    add_panel_label(ax_d, "d")

    fig.subplots_adjust(top=0.97)
    out = MAIN_OUT / "figure_6_external_process_validation"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_supplementary_figure_6(data: dict[str, pd.DataFrame]) -> Path:
    paired = data["climate_paired"].copy()
    phase = data["climate_phase"].copy()
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(8.4, 3.4),
        gridspec_kw={"width_ratios": [1.16, 1.0], "wspace": 0.64},
    )

    ax = axes[0]
    keep = paired[paired["mode"].isin(["oni", "dmi", "nao"])].copy()
    labels = [f"{short_region(r).replace('Eastern & South-Eastern Asia', 'East & SE Asia')}\n{m.upper()}" for r, m in zip(keep["region"], keep["mode"])]
    colors = [BLUE if "Asia" in r else RED for r in keep["region"]]
    x = np.arange(len(keep)) * 1.85
    vals = keep["mean_event_minus_control"].to_numpy(dtype=float)
    ax.bar(x, vals, color=colors, width=0.72)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=28, ha="right", fontsize=6.0)
    ax.set_xlim(x.min() - 0.85, x.max() + 0.85)
    ax.set_ylabel("Event-control mode difference")
    ax.set_ylim(-0.5, 1.0)
    ax.set_yticks(np.arange(-0.5, 1.01, 0.25))
    despine(ax)
    add_panel_label(ax, "a")

    ax = axes[1]
    keep_phase = phase[
        ((phase["region"] == "Eastern and South-Eastern Asia") & (phase["mode"].isin(["oni", "nao"])))
        | ((phase["region"] == "Europe") & (phase["mode"] == "nao"))
    ].copy()
    keep_phase["label"] = keep_phase.apply(lambda r: f"{short_region(r['region'])}\n{r['phase']}", axis=1)
    ax.barh(np.arange(len(keep_phase))[::-1], keep_phase["share_difference"], color=[BLUE if "Asia" in r else RED for r in keep_phase["region"]])
    ax.axvline(0, color="black", lw=0.8, ls="--")
    ax.set_yticks(np.arange(len(keep_phase))[::-1])
    ax.set_yticklabels(keep_phase["label"])
    ax.set_xlabel("Event minus control phase share")
    ax.set_ylim(-0.5, len(keep_phase) - 0.5)
    despine(ax)
    add_panel_label(ax, "b")

    out = SUPP_OUT / "supplementary_figure_s6_climate_modes"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_supplementary_figure_7(data: dict[str, pd.DataFrame]) -> Path:
    perf = data["survivor_perf"].copy()
    contrasts = data["survivor_contrasts"].copy().head(6)
    terms = data["survivor_city_terms"].copy()
    terms = terms[(terms["model"] == "city_augmented_builtform") & (terms["term"].str.startswith("z_"))].copy()
    terms = terms[terms["term"].str.contains("built_surface|green_cover|canopy_height|road_density|compact_share|building_height|natural_share")]
    label_map = {
        "z_built_surface_fraction_2020": "Built-surface fraction",
        "z_mean_building_height_2020": "Building height",
        "z_green_cover_mean_2020": "Green cover",
        "z_canopy_height_mean_2020": "Canopy height",
        "z_road_density_2024": "Road density",
        "z_lcz_compact_share_2025": "Compact LCZ share",
        "z_lcz_natural_share_2025": "Natural local climate zone share",
    }
    terms["label"] = terms["term"].map(label_map)
    terms = terms.dropna(subset=["label"]).copy()

    fig = plt.figure(figsize=(7.35, 5.0))
    gs = fig.add_gridspec(2, 2, hspace=0.54, wspace=0.70)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, :])

    city = perf[perf["model"].isin(["city_base", "city_augmented_builtform"])]
    ax_a.bar(["Base", "Augmented"], city["pseudo_r2"], color=[SLATE, GREEN_DARK])
    ax_a.set_ylabel("City-model pseudo R²")
    ax_a.set_ylim(0, 0.6)
    ax_a.set_yticks(np.arange(0.0, 0.61, 0.1))
    despine(ax_a)
    add_panel_label(ax_a, "a")

    event = perf[perf["model"].isin(["event_base", "event_augmented_builtform"])]
    ax_b.bar(["Base", "Augmented"], event["auc"], color=[SLATE, GREEN_DARK])
    ax_b.set_ylabel("Event-model AUC")
    ax_b.axhline(0.5, color="black", lw=0.8, ls="--")
    ax_b.set_ylim(0, 0.7)
    ax_b.set_yticks(np.arange(0.0, 0.71, 0.1))
    despine(ax_b)
    add_panel_label(ax_b, "b")

    y = np.arange(len(contrasts))[::-1]
    ax_c.barh(y, contrasts["difference_high_minus_low"], color=GREEN_DARK)
    ax_c.axvline(0, color="black", lw=0.8, ls="--")
    ax_c.set_yticks(y)
    ax_c.set_yticklabels(
        [
            "Road density",
            "Built-surface fraction",
            "Building height",
            "High-green fraction",
            "Green cover",
            "Natural local\nclimate zone share",
        ]
    )
    ax_c.set_xlabel("High-failure minus low-failure quartile difference")
    max_abs = max(
        abs(float(contrasts["difference_high_minus_low"].min())),
        abs(float(contrasts["difference_high_minus_low"].max())),
    )
    ax_c.set_xlim(-max_abs * 1.35, max_abs * 1.35)
    ax_c.set_ylim(-0.5, len(contrasts) - 0.5)
    for yi, val in zip(y, contrasts["difference_high_minus_low"]):
        ha = "left" if val >= 0 else "right"
        dx = max_abs * 0.04 if val >= 0 else -max_abs * 0.04
        ax_c.text(val + dx, yi, f"{val:+.3f}", va="center", ha=ha, fontsize=6.5, color=SLATE)
    despine(ax_c)
    add_panel_label(ax_c, "c")

    out = SUPP_OUT / "supplementary_figure_s7_survivor_builtform"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_supplementary_figure_8(data: dict[str, pd.DataFrame]) -> Path:
    global_syn = data["synoptic_global"].copy()
    arch = data["archetypes"].copy()
    proxy = data["proxy_perf"].copy()

    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.4), gridspec_kw={"wspace": 0.90})

    ax = axes[0]
    keep = global_syn[global_syn["metric"].isin(["z500_gpm", "omega700_pa_s", "swvl_mean_m3_m3"])].copy()
    label_map = {"z500_gpm": "Z500", "omega700_pa_s": "700 hPa\nvertical velocity", "swvl_mean_m3_m3": "Soil moisture"}
    vals = []
    labels = []
    for row in keep.itertuples(index=False):
        value = row.mean_event_minus_control
        if row.metric == "swvl_mean_m3_m3":
            value = -value
        vals.append(value)
        labels.append(label_map[row.metric])
    x = np.arange(len(labels)) * 1.25
    ax.bar(x, vals, color=[BLUE, RED, GOLD], width=0.68)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.set_ylabel("Pooled event-control contrast")
    ax.set_ylim(0, 5.0)
    ax.set_yticks([0, 1, 2, 3, 4, 5])
    for xi, val in zip(x, vals):
        y_text = min(val + 0.05, 4.92)
        ax.text(xi, y_text, f"{val:+.3f}", ha="center", va="bottom", fontsize=6.4)
    despine(ax)
    add_panel_label(ax, "a")

    ax = axes[1]
    x = np.arange(len(arch)) * 1.55
    arch_labels = {
        "persistent_dry_hot_humid": "Persistent\ndry-hot\nhumid",
        "mixed_failure_pathway": "Mixed\nfailure\npathway",
    }
    ax.bar(x, arch["n_events"], color=[RED, BLUE], width=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([arch_labels.get(v, v) for v in arch["archetype_label"]], rotation=0, ha="center")
    ax.set_ylabel("Number of events")
    ax.set_ylim(0, 30)
    ax.set_yticks([0, 10, 20, 30])
    for xi, val in zip(x, arch["n_events"]):
        ax.text(xi, min(float(val) + 0.6, 29.2), f"{int(val)}", ha="center", va="bottom", fontsize=6.5)
    despine(ax)
    add_panel_label(ax, "b")

    ax = axes[2]
    labels_c = ["Top 5\nbaseline", "Top 5\n+ regime", "Top 10\nbaseline", "Top 10\n+ regime"]
    x = np.arange(len(labels_c)) * 1.52
    ax.bar(x, proxy["pseudo_r2_mcfadden"], width=0.70, color=[SLATE, GREEN_DARK, SLATE, GREEN_DARK])
    ax.set_xticks(x)
    ax.set_xticklabels(labels_c, rotation=0, ha="center")
    ax.set_ylabel("Pseudo R²")
    ax.set_ylim(0, 0.9)
    ax.set_yticks([0.0, 0.3, 0.6, 0.9])
    for xi, val in zip(x, proxy["pseudo_r2_mcfadden"]):
        ax.text(xi, min(float(val) + 0.025, 0.895), f"{val:.3f}", ha="center", va="bottom", fontsize=6.4)
    despine(ax)
    add_panel_label(ax, "c")

    out = SUPP_OUT / "supplementary_figure_s8_global_archetypes"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def make_supplementary_figure_9(data: dict[str, pd.DataFrame]) -> Path:
    profiles = data["conditional_profiles"].copy()
    night = data["night_process"].copy()
    night = night[night["region"] == "Eastern and South-Eastern Asia"].copy()

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.5), gridspec_kw={"wspace": 0.82})

    ax = axes[0]
    order = [
        "water_supported_low_retention",
        "water_supported_high_retention",
        "water_limited_low_retention",
        "water_limited_high_retention",
    ]
    label_map = {
        "water_supported_low_retention": "Supported\nLow retention",
        "water_supported_high_retention": "Supported\nHigh retention",
        "water_limited_low_retention": "Limited\nLow retention",
        "water_limited_high_retention": "Limited\nHigh retention",
    }
    colors = [GREEN_LIGHT, GREEN_DARK, GOLD, RED]
    s = profiles.set_index("profile").loc[order].reset_index()
    x = np.arange(len(s)) * 1.28
    ax.bar(x, s["predicted_failure_probability"], color=colors, width=0.76)
    ax.set_xticks(x)
    ax.set_xticklabels([label_map[k] for k in s["profile"]], rotation=20, ha="right")
    ax.set_ylabel("Predicted failure probability")
    ax.set_ylim(0, 0.6)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6])
    despine(ax)
    add_panel_label(ax, "a")

    ax = axes[1]
    keep = night[night["metric"].isin(["t2m_true_night_c", "d2m_true_night_c", "wind10_true_night_ms", "skt_true_night_c", "skin_air_gap_true_night_c"])].copy()
    label_map_n = {
        "t2m_true_night_c": "True-night air",
        "d2m_true_night_c": "True-night dewpoint",
        "wind10_true_night_ms": "Weaker wind",
        "skt_true_night_c": "Surface skin",
        "skin_air_gap_true_night_c": "Skin-air gap",
    }
    keep["effect"] = keep.apply(
        lambda r: (-r["mean_event_minus_control"] if r["metric"] == "wind10_true_night_ms" else r["mean_event_minus_control"])
        / (r["std_event_minus_control"] if pd.notna(r["std_event_minus_control"]) and r["std_event_minus_control"] not in (0.0,) else np.nan),
        axis=1,
    )
    keep["label"] = keep["metric"].map(label_map_n)
    label_order = ["True-night air", "True-night dewpoint", "Surface skin", "Skin-air gap", "Weaker wind"]
    keep = keep.set_index("label").loc[label_order]
    y = np.arange(len(keep))[::-1]
    bar_colors = [BLUE, TEAL, RED, GOLD, SLATE]
    ax.barh(y, keep["effect"], color=bar_colors)
    ax.axvline(0, color="black", lw=0.8, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels(keep.index)
    ax.set_xlabel("Standardized event-control contrast")
    ax.set_ylim(-0.5, len(keep) - 0.5)
    despine(ax)
    add_panel_label(ax, "b")

    out = SUPP_OUT / "supplementary_figure_s9_conditional_night_process"
    save_figure(fig, out)
    plt.close(fig)
    return out.with_suffix(".png")


def write_manifest(paths: list[Path]) -> Path:
    manifest = pd.DataFrame({"figure_file": [p.name for p in paths], "absolute_path": [str(p) for p in paths]})
    out = OUT_ROOT / "figure_manifest.csv"
    manifest.to_csv(out, index=False)
    return out


def main() -> None:
    set_nature_style()
    MAIN_OUT.mkdir(parents=True, exist_ok=True)
    SUPP_OUT.mkdir(parents=True, exist_ok=True)
    data = main_inputs()
    outputs = [
        make_figure_1(data),
        make_figure_2(data),
        make_figure_3(data),
        make_figure_4(data),
        make_figure_6(data),
        make_supplementary_figure_6(data),
        make_supplementary_figure_7(data),
        make_supplementary_figure_8(data),
        make_supplementary_figure_9(data),
    ]
    manifest = write_manifest(outputs)
    print("Wrote display items:")
    for out in outputs:
        print(" -", out)
    print("Manifest:", manifest)


if __name__ == "__main__":
    main()
