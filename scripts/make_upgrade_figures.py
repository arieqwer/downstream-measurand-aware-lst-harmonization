from pathlib import Path
from typing import Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/analysis_outputs"
FIG = ROOT / "outputs/figures/main"
SOURCE = ROOT / "data/processed/figure_source_data"

GREEN = "#176B4D"
GREEN_LIGHT = "#8DBF9E"
OLIVE = "#A5A66F"
BLUE = "#277DA1"
ORANGE = "#E58C32"
RED = "#C43D2B"
GOLD = "#D7A315"
INK = "#172126"
GRAY = "#65727E"
LIGHT = "#E8EDF0"
STATE_COLORS = {
    "mld": GREEN_LIGHT,
    "dhd": ORANGE,
    "extreme_dhd": RED,
}
STATE_LABELS = {
    "mld": "Moist-low\ndemand",
    "dhd": "Dry-high\ndemand",
    "extreme_dhd": "Extreme\ndry-high demand",
}


def setup() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    mpl.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 9,
            "axes.labelsize": 10,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "axes.linewidth": 0.8,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "xtick.major.size": 3.5,
            "ytick.major.size": 3.5,
            "legend.fontsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
        }
    )


def clean_axis(ax: plt.Axes, grid: Optional[str] = None) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def label_panel(ax: plt.Axes, label: str, x: float = -0.12, y: float = 1.05) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        color=INK,
    )


def save(fig: plt.Figure, name: str) -> None:
    for suffix, kwargs in [
        ("png", {"dpi": 600}),
        ("pdf", {}),
        ("svg", {}),
    ]:
        fig.savefig(FIG / f"{name}.{suffix}", **kwargs)
    plt.close(fig)


def city_level_state_summary() -> pd.DataFrame:
    return pd.read_csv(SOURCE / "figures_1_2_city_state_summary.csv")


def figure1(summary: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(7.3, 6.15))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1], width_ratios=[1.10, 0.90], hspace=0.62, wspace=0.42)
    ax_map = fig.add_subplot(gs[0, :])
    ax_method = fig.add_subplot(gs[1, 0])
    ax_state = fig.add_subplot(gs[1, 1])

    mapped = pd.read_csv(SOURCE / "figure_1a_city_locations.csv", dtype={"uc_id": str})
    for value, color, label, zorder in [
        (0, OLIVE, "Lower vegetation support", 1),
        (1, GREEN, "Higher vegetation support", 2),
    ]:
        subset = mapped[mapped["high_green"].eq(value)]
        ax_map.scatter(subset["lon"], subset["lat"], s=2.3, c=color, alpha=0.62, linewidths=0, label=label, zorder=zorder)
    ax_map.set_xlim(-180, 180)
    ax_map.set_ylim(-60, 75)
    ax_map.set_xticks(np.arange(-180, 181, 60))
    ax_map.set_yticks(np.arange(-60, 76, 15))
    ax_map.set_xlabel("Longitude")
    ax_map.set_ylabel("Latitude")
    ax_map.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.13),
        frameon=False,
        ncol=2,
        handletextpad=0.5,
        columnspacing=1.5,
        markerscale=3.8,
    )
    clean_axis(ax_map)
    label_panel(ax_map, "a", -0.06, 1.03)

    ax_method.set_axis_off()
    label_panel(ax_method, "b", -0.07, 1.03)
    box_kw = dict(boxstyle="round,pad=0.02,rounding_size=0.025", ec=GRAY, lw=1.0)
    boxes = [
        (0.03, 0.68, 0.42, 0.20, "MODIS daytime\nbuilt-associated LST", "#F7DFC3"),
        (0.55, 0.68, 0.42, 0.20, "MODIS nighttime\nbuilt-associated LST", "#D8E8F3"),
        (0.04, 0.17, 0.92, 0.31, "Apparent day-to-night LST decay rate\n$r_u=\\ln(T_{day,u,K}/T_{night,u,K})/12\\,h$\nCore-minus-ring differential: $\\Delta r=r_{core}-r_{ring}$", "#DCECE2"),
    ]
    for x, y, w, h, text, face in boxes:
        patch = FancyBboxPatch((x, y), w, h, transform=ax_method.transAxes, fc=face, **box_kw)
        ax_method.add_patch(patch)
        ax_method.text(x + w / 2, y + h / 2, text, transform=ax_method.transAxes, ha="center", va="center", fontsize=8.2)
    ax_method.add_patch(FancyArrowPatch((0.24, 0.66), (0.24, 0.50), transform=ax_method.transAxes, arrowstyle="-|>", mutation_scale=10, lw=1.0, color=GRAY))
    ax_method.add_patch(FancyArrowPatch((0.76, 0.66), (0.76, 0.50), transform=ax_method.transAxes, arrowstyle="-|>", mutation_scale=10, lw=1.0, color=GRAY))
    ax_method.text(0.50, 0.06, "Positive Δr: larger apparent LST decrease in the core", transform=ax_method.transAxes, ha="center", va="center", fontsize=7.7, color=GRAY)

    label_panel(ax_state, "c", -0.16, 1.03)
    state = summary[(summary["high_green"].eq(1))].set_index("analysis_state").loc[list(STATE_LABELS)]
    x = np.arange(3)
    means = state["mean_differential_decay"].to_numpy()
    errors = 1.96 * state["se_differential_decay"].to_numpy()
    ax_state.bar(x, means, yerr=errors, color=[STATE_COLORS[s] for s in STATE_LABELS], width=0.66, capsize=3, edgecolor="white", linewidth=0.8)
    ax_state.axhline(0, color=INK, lw=0.9)
    ax_state.set_xticks(x, [STATE_LABELS[s] for s in STATE_LABELS])
    ax_state.set_ylabel("Core-minus-ring decay-rate differential\n" + r"($10^{-4}$ h$^{-1}$)")
    ax_state.set_ylim(-0.55, 1.05)
    ax_state.set_yticks(np.arange(-0.5, 1.01, 0.25))
    clean_axis(ax_state, "y")
    for xi, value, error in zip(x, means, errors):
        if value >= 0:
            y = value + error + 0.06
            va = "bottom"
        else:
            y = value - error - 0.05
            va = "top"
        ax_state.text(xi, y, f"{value:+.2f}", ha="center", va=va, fontsize=8, color=INK)

    save(fig, "Figure_1_global_differential_decay_framework")


def figure2(summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.3, 6.35), gridspec_kw={"hspace": 0.48, "wspace": 0.42})
    fig.subplots_adjust(top=0.88)
    ax_raw, ax_anom, ax_quant, ax_transition = axes.ravel()
    high = summary[summary["high_green"].eq(1)].set_index("analysis_state").loc[list(STATE_LABELS)]
    x = np.array([0, 1])
    for state in STATE_LABELS:
        row = high.loc[state]
        y = [row["mean_raw_day"], row["mean_raw_night"]]
        e = 1.96 * np.array([row["se_raw_day"], row["se_raw_night"]])
        ax_raw.plot(x, y, color=STATE_COLORS[state], marker="o", lw=2, ms=4, label=STATE_LABELS[state].replace("\n", " "))
        ax_raw.errorbar(x, y, yerr=e, fmt="none", ecolor=STATE_COLORS[state], capsize=2, lw=0.9)
    ax_raw.set_xticks(x, ["Daytime", "Nighttime"])
    ax_raw.set_ylabel("Built-associated core − ring LST (°C)")
    ax_raw.set_ylim(0.35, 0.88)
    handles, labels = ax_raw.get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=3, columnspacing=1.0, handlelength=1.8)
    clean_axis(ax_raw, "y")
    label_panel(ax_raw, "a")

    for state in STATE_LABELS:
        row = high.loc[state]
        y = [row["mean_anom_day"], row["mean_anom_night"]]
        e = 1.96 * np.array([row["se_anom_day"], row["se_anom_night"]])
        ax_anom.plot(x, y, color=STATE_COLORS[state], marker="o", lw=2, ms=4)
        ax_anom.errorbar(x, y, yerr=e, fmt="none", ecolor=STATE_COLORS[state], capsize=2, lw=0.9)
    ax_anom.axhline(0, color=INK, lw=0.8)
    ax_anom.set_xticks(x, ["Daytime", "Nighttime"])
    ax_anom.set_ylabel("Core − ring climatological LST anomaly (°C)")
    ax_anom.set_ylim(-0.28, 0.16)
    clean_axis(ax_anom, "y")
    label_panel(ax_anom, "b")

    quant = pd.read_csv(OUT / "matched_distributional_quantile_results.csv")
    quant = quant[(quant["minimum_intervals_per_state"].eq(10)) & quant["contrast"].eq("dhd_minus_mld")].copy()
    quant = quant.sort_values("quantile")
    yq = np.arange(len(quant))
    ax_quant.errorbar(
        quant["matched_high_minus_low_shift"],
        yq,
        xerr=[
            quant["matched_high_minus_low_shift"] - quant["bootstrap_ci95_low"],
            quant["bootstrap_ci95_high"] - quant["matched_high_minus_low_shift"],
        ],
        fmt="o",
        color=GREEN,
        ecolor=GREEN,
        capsize=3,
        lw=1.2,
    )
    ax_quant.set_yticks(yq, [f"Q{int(q * 100)}" for q in quant["quantile"]])
    ax_quant.set_xlabel("Matched high-minus-low DHD–MLD shift (°C)")
    ax_quant.set_ylabel("Nighttime anomaly quantile")
    ax_quant.set_xlim(0, 0.14)
    clean_axis(ax_quant, "x")
    label_panel(ax_quant, "c")

    trans = pd.read_csv(OUT / "matched_transition_results.csv")
    trans = trans[trans["anomaly_threshold_c"].isin([0.1, 0.25, 0.5])].copy()
    for outcome, color, marker, label in [
        ("onset_shift_dhd_minus_mld", BLUE, "o", "Onset"),
        ("persistence_shift_dhd_minus_mld", RED, "s", "Persistence"),
    ]:
        subset = trans[trans["outcome"].eq(outcome)].sort_values("anomaly_threshold_c")
        ax_transition.errorbar(
            subset["anomaly_threshold_c"],
            subset["matched_high_minus_low_dhd_mld_shift"],
            yerr=[
                subset["matched_high_minus_low_dhd_mld_shift"] - subset["bootstrap_ci95_low"],
                subset["bootstrap_ci95_high"] - subset["matched_high_minus_low_dhd_mld_shift"],
            ],
            color=color,
            marker=marker,
            lw=1.5,
            capsize=3,
            label=label,
        )
    ax_transition.set_xticks([0.1, 0.25, 0.5])
    ax_transition.set_xlabel("Day-to-night inversion threshold (°C)")
    ax_transition.set_ylabel("Matched high-minus-low probability shift")
    ax_transition.set_ylim(0, 0.052)
    ax_transition.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2)
    clean_axis(ax_transition, "y")
    label_panel(ax_transition, "d")

    save(fig, "Figure_2_upper_tail_state_transitions")


def figure3() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.3, 6.25), gridspec_kw={"hspace": 0.50, "wspace": 0.70})
    ax_load, ax_quart, ax_water, ax_mod = axes.ravel()

    load = pd.read_csv(OUT / "built_form_storage_score_loadings.csv")
    labels = {
        "built_surface_fraction_2020": "Built-surface fraction",
        "mean_building_height_2020": "Mean building height",
        "road_density_2024": "Road density",
        "lcz_compact_share_2025": "Compact LCZ share",
    }
    load["label"] = load["feature"].map(labels)
    load = load.sort_values("pc1_loading")
    ax_load.barh(load["label"], load["pc1_loading"], color=GREEN)
    ax_load.set_xlabel("PC1 loading")
    ax_load.set_xlim(0, 0.70)
    clean_axis(ax_load, "x")
    label_panel(ax_load, "a")

    quart = pd.read_csv(OUT / "differential_thermal_decay_storage_quartiles.csv")
    order = ["Q1 lowest", "Q2", "Q3", "Q4 highest"]
    for contrast, color, marker, label in [
        ("dhd_minus_mld", ORANGE, "o", "DHD − MLD"),
        ("extreme_dhd_minus_mld", RED, "s", "Extreme DHD − MLD"),
    ]:
        subset = quart[quart["contrast"].eq(contrast)].set_index("storage_quartile").loc[order]
        x = np.arange(4)
        ax_quart.errorbar(x, subset["mean_differential_decay_shift_1e4_h"], yerr=1.96 * subset["standard_error"], marker=marker, color=color, lw=1.6, capsize=3, label=label)
    ax_quart.set_xticks(np.arange(4), ["Q1\nlowest", "Q2", "Q3", "Q4\nhighest"])
    ax_quart.set_xlabel("Morphology-based heat-retention quartile")
    ax_quart.set_ylabel(r"Stress-minus-MLD decay-rate shift ($10^{-4}$ h$^{-1}$)")
    ax_quart.set_ylim(-1.9, 0.15)
    ax_quart.legend(frameon=False, loc="upper right")
    clean_axis(ax_quart, "y")
    label_panel(ax_quart, "b")

    water = pd.read_csv(OUT / "differential_decay_water_support_heterogeneity.csv")
    water["water_support_tertile"] = water["water_support_tertile"].str.title().replace({"Middle": "Intermediate"})
    water_order = ["Low", "Intermediate", "High"]
    for term, color, marker, label in [
        ("dhd_x_built_form_storage_score", ORANGE, "o", "DHD"),
        ("extreme_x_built_form_storage_score", RED, "s", "Extreme DHD"),
    ]:
        subset = water[water["term"].eq(term)].set_index("water_support_tertile").loc[water_order]
        x = np.arange(3)
        ax_water.errorbar(
            x,
            subset["estimate"],
            yerr=[subset["estimate"] - subset["ci95_low"], subset["ci95_high"] - subset["estimate"]],
            marker=marker,
            color=color,
            lw=1.6,
            capsize=3,
            label=label,
        )
    ax_water.set_xticks(np.arange(3), ["Low", "Intermediate", "High"])
    ax_water.set_xlabel("Long-term water-support tertile")
    ax_water.set_ylabel("Heat-retention interaction on Δr\n" + r"($10^{-4}$ h$^{-1}$ per SD)")
    ax_water.set_ylim(-1.12, 0.03)
    ax_water.legend(frameon=False, loc="upper right")
    clean_axis(ax_water, "y")
    label_panel(ax_water, "c")

    terms = pd.read_csv(OUT / "differential_thermal_decay_twfe_terms.csv")
    selectors = [
        ("built_form_storage_score", "Morphology-based\nheat retention"),
        ("z_ventilation_obstruction_index", "Ventilation\nobstruction"),
        ("z_ahe_night_wm2", "Nighttime\nanthropogenic heat"),
    ]
    rows = []
    for key, label in selectors:
        subset = terms[(terms["model"].str.contains(key, regex=False)) & terms["term"].str.contains(key, regex=False)]
        for _, row in subset.iterrows():
            rows.append({**row.to_dict(), "label": label, "state": "Extreme DHD" if row["term"].startswith("extreme") else "DHD"})
    mod = pd.DataFrame(rows)
    ybase = np.arange(len(selectors))[::-1]
    offsets = {"DHD": -0.11, "Extreme DHD": 0.11}
    colors = {"DHD": ORANGE, "Extreme DHD": RED}
    for state in ["DHD", "Extreme DHD"]:
        subset = mod[mod["state"].eq(state)].set_index("label").loc[[x[1] for x in selectors]]
        y = ybase + offsets[state]
        ax_mod.errorbar(
            subset["estimate"],
            y,
            xerr=[subset["estimate"] - subset["ci95_low"], subset["ci95_high"] - subset["estimate"]],
            fmt="o" if state == "DHD" else "s",
            color=colors[state],
            capsize=3,
            lw=1.2,
            label=state,
        )
    ax_mod.set_yticks(ybase, [x[1] for x in selectors])
    ax_mod.set_xlabel(r"Interaction on Δr ($10^{-4}$ h$^{-1}$ per SD)")
    ax_mod.set_xlim(-0.65, 0.03)
    ax_mod.legend(frameon=False, loc="upper right", handlelength=2.8)
    clean_axis(ax_mod, "x")
    label_panel(ax_mod, "d")

    save(fig, "Figure_3_coupled_water_built_form_mechanism")


def figure4() -> None:
    fig = plt.figure(figsize=(7.3, 5.25))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.08], hspace=0.48, wspace=0.43)
    ax_duration = fig.add_subplot(gs[0, 0])
    ax_memory = fig.add_subplot(gs[0, 1])
    ax_sync = fig.add_subplot(gs[1, :])

    memory = pd.read_csv(OUT / "stress_memory_twfe_terms.csv")
    duration = memory[memory["model"].eq("dhd_duration_differential_decay_1e4_h")]
    duration = duration[duration["term"].isin(["duration_excess_capped", "duration_x_storage"])].copy()
    duration["label"] = duration["term"].map(
        {
            "duration_excess_capped": "Each additional DHD\ninterval (1–5)",
            "duration_x_storage": "Duration × morphology-based\nheat retention",
        }
    )
    yd = np.arange(len(duration))[::-1]
    ax_duration.errorbar(
        duration["estimate"],
        yd,
        xerr=[duration["estimate"] - duration["ci95_low"], duration["ci95_high"] - duration["estimate"]],
        fmt="o",
        color=GREEN,
        capsize=3,
        lw=1.3,
    )
    ax_duration.set_yticks(yd, duration["label"])
    ax_duration.set_xlabel(r"Decay-rate differential change ($10^{-4}$ h$^{-1}$)")
    ax_duration.set_xlim(-0.11, 0)
    clean_axis(ax_duration, "x")
    label_panel(ax_duration, "a", -0.20, 1.09)

    post = memory[memory["model"].eq("post_dhd_memory_inversion_0p25")].copy()
    post = post[post["term"].str.fullmatch(r"post_dhd_lag[1-4]")].copy()
    post["lag"] = post["term"].str.extract(r"(\d+)").astype(int)
    post = post.sort_values("lag")
    significant = post["p_value_holm_within_model"] < 0.05
    ax_memory.errorbar(
        post["lag"] * 8,
        post["estimate"],
        yerr=[post["estimate"] - post["ci95_low"], post["ci95_high"] - post["estimate"]],
        fmt="none",
        ecolor=RED,
        capsize=3,
        lw=1.2,
    )
    ax_memory.scatter(post.loc[significant, "lag"] * 8, post.loc[significant, "estimate"], color=RED, s=28, zorder=3, label="Holm-adjusted P < 0.05")
    ax_memory.scatter(post.loc[~significant, "lag"] * 8, post.loc[~significant, "estimate"], facecolor="white", edgecolor=RED, s=28, zorder=3, label="Not significant")
    ax_memory.set_xticks([8, 16, 24, 32])
    ax_memory.set_xlabel("Time after DHD ended (days)")
    ax_memory.set_ylabel("Excess severe inversion probability")
    ax_memory.set_ylim(-0.0003, 0.0072)
    ax_memory.spines["bottom"].set_position(("data", 0))
    ax_memory.legend(frameon=False, loc="upper right", fontsize=7.2)
    clean_axis(ax_memory, "y")
    label_panel(ax_memory, "b", -0.18, 1.09)

    intervals = pd.read_csv(OUT / "corrected_inversion_concurrence_intervals.csv")
    severe = intervals[intervals["inversion_threshold_c"].eq(0.25)].copy()
    annual = severe.groupby("year", as_index=False).agg(
        maximum_concurrent_population=("concurrent_represented_population", "max"),
        mean_concurrent_population=("concurrent_represented_population", "mean"),
    )
    annual["maximum_million"] = annual["maximum_concurrent_population"] / 1e6
    annual["mean_million"] = annual["mean_concurrent_population"] / 1e6
    ax_sync.plot(annual["year"], annual["maximum_million"], color=GREEN, lw=2.2, marker="o", ms=3.2, label="Annual maximum")
    ax_sync.plot(annual["year"], annual["mean_million"], color=GREEN, lw=1.5, ls="--", label="Annual mean")
    peak = annual.loc[annual["maximum_million"].idxmax()]
    ax_sync.scatter([peak["year"]], [peak["maximum_million"]], s=48, color=RED, zorder=4)
    ax_sync.annotate(
        f"{peak['maximum_million']:.1f} million\n(2024, one 8-day interval)",
        xy=(peak["year"], peak["maximum_million"]),
        xytext=(peak["year"] - 5.5, peak["maximum_million"] + 8),
        arrowprops={"arrowstyle": "-", "color": GRAY, "lw": 0.9},
        ha="left",
        va="bottom",
        fontsize=8,
    )
    ax_sync.set_xlim(2002.5, 2025.5)
    ax_sync.set_xticks([2003, 2007, 2011, 2015, 2019, 2023])
    ax_sync.set_ylim(0, 122)
    ax_sync.set_ylabel("Concurrent represented population (million)")
    ax_sync.set_xlabel("Year")
    ax_sync.legend(frameon=False, loc="upper left", ncol=2)
    clean_axis(ax_sync, "y")
    label_panel(ax_sync, "c", -0.08, 1.06)

    save(fig, "Figure_4_stress_accumulation_memory_concurrence")


def main() -> None:
    setup()
    summary = city_level_state_summary()
    figure1(summary)
    figure2(summary)
    figure3()
    figure4()
    print(f"Figures written to {FIG}")


if __name__ == "__main__":
    main()
