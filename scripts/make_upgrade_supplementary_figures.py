from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from make_upgrade_figures import (
    BLUE,
    GRAY,
    GREEN,
    INK,
    OLIVE,
    ORANGE,
    RED,
    ROOT,
    STATE_LABELS,
    clean_axis,
    label_panel,
    setup,
)


OUT = ROOT / "data/processed/analysis_outputs"
FIG = ROOT / "outputs/figures/supplementary"


def save(fig: plt.Figure, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for suffix, kwargs in [("png", {"dpi": 600}), ("pdf", {}), ("svg", {})]:
        fig.savefig(FIG / f"{name}.{suffix}", **kwargs)
    plt.close(fig)


def supplementary_1() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 6.25), gridspec_kw={"hspace": 0.52, "wspace": 0.64})
    ax_valid, ax_balance, ax_match, ax_green = axes.ravel()

    valid = pd.read_csv(OUT / "observation_validity_audit.csv")
    states = ["mld", "dhd", "extreme_dhd"]
    x = np.arange(3)
    for group, color, offset, label in [
        ("low_veg", OLIVE, -0.18, "Lower vegetation support"),
        ("high_veg", GREEN, 0.18, "Higher vegetation support"),
    ]:
        subset = valid[valid["veg_group"].eq(group)].set_index("analysis_state").loc[states]
        ax_valid.bar(x + offset, subset["valid_fraction"], width=0.34, color=color, label=label)
    ax_valid.set_xticks(x, [STATE_LABELS[s] for s in states])
    ax_valid.set_ylim(0.75, 0.96)
    ax_valid.set_ylabel("Valid paired core–ring fraction")
    ax_valid.legend(frameon=False, loc="lower right", fontsize=7.2)
    clean_axis(ax_valid, "y")
    label_panel(ax_valid, "a")

    balance = pd.read_csv(OUT / "optimal_matching_balance.csv")
    balance_labels = {
        "log_population": "Log population",
        "median_true_night_t2m_c": "True-night 2-m temperature",
        "median_true_night_wetbulb_c": "True-night wet-bulb",
        "mean_vpd_kpa": "VPD",
        "mean_rzsm": "Root-zone soil moisture",
        "mean_log1p_pr_sum": "Precipitation",
        "mean_gradient_mld": "MLD nighttime contrast",
        "valid_core_ring_fraction": "Valid core–ring fraction",
    }
    balance["label"] = balance["covariate"].map(balance_labels)
    y = np.arange(len(balance))[::-1]
    ax_balance.scatter(balance["standardized_difference_before"].abs(), y, color=GRAY, s=25, label="Before")
    ax_balance.scatter(balance["standardized_difference_after"].abs(), y, color=GREEN, s=25, label="After")
    ax_balance.axvline(0.1, color=RED, ls="--", lw=0.9)
    ax_balance.set_yticks(y, balance["label"], fontsize=7.2)
    ax_balance.set_xlabel("Absolute standardized difference")
    ax_balance.legend(frameon=False, loc="lower right")
    clean_axis(ax_balance, "x")
    label_panel(ax_balance, "b")

    matched = pd.read_csv(OUT / "matched_differential_thermal_decay_results.csv")
    matched["label"] = matched["contrast"].map({"dhd_minus_mld": "DHD − MLD", "extreme_dhd_minus_mld": "Extreme DHD − MLD"})
    ym = np.arange(len(matched))[::-1]
    ax_match.errorbar(
        matched["matched_high_minus_low_differential_decay_shift_1e4_h"],
        ym,
        xerr=[
            matched["matched_high_minus_low_differential_decay_shift_1e4_h"] - matched["bootstrap_ci95_low"],
            matched["bootstrap_ci95_high"] - matched["matched_high_minus_low_differential_decay_shift_1e4_h"],
        ],
        fmt="o",
        color=GREEN,
        capsize=3,
    )
    ax_match.axvline(0, color=INK, lw=0.8)
    ax_match.set_yticks(ym, matched["label"])
    ax_match.set_xlabel(r"Matched high-minus-low decay shift ($10^{-4}$ h$^{-1}$)")
    ax_match.set_xlim(-0.26, 0.06)
    clean_axis(ax_match, "x")
    label_panel(ax_match, "c")

    terms = pd.read_csv(OUT / "differential_thermal_decay_twfe_terms.csv")
    continuous = terms[
        terms["model"].eq("differential_decay_continuous_green_support")
        & terms["term"].isin(["dhd_x_green_support", "extreme_x_green_support"])
    ].copy()
    continuous["label"] = continuous["term"].map(
        {"dhd_x_green_support": "DHD × vegetation support", "extreme_x_green_support": "Extreme DHD × vegetation support"}
    )
    yg = np.arange(len(continuous))[::-1]
    ax_green.errorbar(
        continuous["estimate"],
        yg,
        xerr=[continuous["estimate"] - continuous["ci95_low"], continuous["ci95_high"] - continuous["estimate"]],
        fmt="o",
        color=GREEN,
        capsize=3,
    )
    ax_green.axvline(0, color=INK, lw=0.8)
    ax_green.set_yticks(yg, continuous["label"])
    ax_green.set_xlabel(r"Vegetation-support interaction ($10^{-4}$ h$^{-1}$ SD$^{-1}$)")
    clean_axis(ax_green, "x")
    label_panel(ax_green, "d")

    save(fig, "Figure_S1_validity_matching_continuous_support")


def supplementary_2() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.3, 6.25), gridspec_kw={"hspace": 0.52, "wspace": 0.52})
    ax_all, ax_hot, ax_sampling, ax_ring = axes.ravel()
    state = pd.read_csv(OUT / "differential_thermal_decay_state_summary.csv")
    state = state[state["weighting"].eq("city")]
    colors = {0: OLIVE, 1: GREEN}
    labels = {0: "Lower vegetation support", 1: "Higher vegetation support"}
    x = np.arange(3)
    for ax, sample, panel in [(ax_all, "all_intervals", "a"), (ax_hot, "true_night_heat_intervals", "b")]:
        subset = state[state["sample"].eq(sample)]
        for group in [0, 1]:
            values = subset[subset["high_green"].eq(group)].set_index("analysis_state").loc[list(STATE_LABELS)]
            ax.errorbar(
                x,
                values["mean_differential_decay_1e4_h"],
                yerr=1.96 * values["se_differential_decay_1e4_h"],
                marker="o" if group else "s",
                color=colors[group],
                lw=1.7,
                capsize=3,
                label=labels[group],
            )
        ax.axhline(0, color=INK, lw=0.8)
        ax.set_xticks(x, [STATE_LABELS[s] for s in STATE_LABELS])
        ax.set_ylabel(r"Core − ring apparent decay ($10^{-4}$ h$^{-1}$)")
        ax.legend(frameon=False, loc="upper right", fontsize=7.2)
        clean_axis(ax, "y")
        label_panel(ax, panel)
    ax_all.set_title("All paired intervals", fontsize=9.5)
    ax_hot.set_title("True-night heat intervals", fontsize=9.5)

    sampling = pd.read_csv(OUT / "differential_thermal_decay_sampling_sensitivity.csv")
    sampling = sampling[sampling["term"].eq("dhd_x_built_form_storage_score")].copy()
    sampling["label"] = sampling["model"].map(
        {
            "minimum_5_built_pixels": "≥5 built pixels",
            "minimum_10_built_pixels": "≥10 built pixels",
            "minimum_20_built_pixels": "≥20 built pixels",
            "maximum_0.25_day_night_count_imbalance": "≤25% day/night imbalance",
            "maximum_0.10_day_night_count_imbalance": "≤10% day/night imbalance",
            "maximum_0.05_day_night_count_imbalance": "≤5% day/night imbalance",
        }
    )
    ys = np.arange(len(sampling))[::-1]
    ax_sampling.errorbar(
        sampling["estimate"],
        ys,
        xerr=[sampling["estimate"] - sampling["ci95_low"], sampling["ci95_high"] - sampling["estimate"]],
        fmt="o",
        color=GREEN,
        capsize=3,
    )
    ax_sampling.axvline(0, color=INK, lw=0.8)
    ax_sampling.set_yticks(ys, sampling["label"])
    ax_sampling.set_xlabel(r"DHD × storage-proxy coefficient ($10^{-4}$ h$^{-1}$ per SD)")
    clean_axis(ax_sampling, "x")
    label_panel(ax_sampling, "c")

    rings = pd.read_csv(OUT / "corrected_alt_ring_sensitivity.csv")
    rings = rings[(rings["contrast"].eq("dhd_minus_mld")) & rings["outcome"].eq("core_minus_ring_tb_night_anom")].copy()
    rings["label"] = rings["ring_definition"].map({"ring5_15": "5–15 km", "ring10_20": "10–20 km", "ring20_30": "20–30 km"})
    rings = rings.set_index("label").loc[["5–15 km", "10–20 km", "20–30 km"]].reset_index()
    yr = np.arange(len(rings))[::-1]
    ax_ring.errorbar(
        rings["matched_high_minus_low_shift"],
        yr,
        xerr=[rings["matched_high_minus_low_shift"] - rings["bootstrap_ci95_low"], rings["bootstrap_ci95_high"] - rings["matched_high_minus_low_shift"]],
        fmt="o",
        color=GREEN,
        capsize=3,
    )
    ax_ring.axvline(0, color=INK, lw=0.8)
    ax_ring.set_yticks(yr, rings["label"])
    ax_ring.set_xlabel("Matched DHD–MLD nighttime-anomaly shift (°C)")
    clean_axis(ax_ring, "x")
    label_panel(ax_ring, "d")
    save(fig, "Figure_S2_state_sampling_ring_sensitivity")


def supplementary_3() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 6.55), gridspec_kw={"hspace": 0.55, "wspace": 0.82})
    ax_components, ax_regions, ax_period, ax_coupled = axes.ravel()

    components = pd.read_csv(OUT / "built_form_component_interactions.csv")
    comp_names = {
        "built_surface_fraction_2020": "Built-surface fraction",
        "mean_building_height_2020": "Mean building height",
        "road_density_2024": "Road density",
        "lcz_compact_share_2025": "Compact LCZ share",
    }
    components["label"] = components["model"].map(comp_names)
    components["state"] = np.where(components["term"].str.startswith("extreme"), "Extreme DHD", "DHD")
    base = np.arange(4)[::-1]
    for state_name, color, marker, offset in [("DHD", ORANGE, "o", -0.10), ("Extreme DHD", RED, "s", 0.10)]:
        subset = components[components["state"].eq(state_name)].set_index("label").loc[list(comp_names.values())]
        ax_components.errorbar(
            subset["estimate"], base + offset,
            xerr=[subset["estimate"] - subset["ci95_low"], subset["ci95_high"] - subset["estimate"]],
            fmt=marker, color=color, capsize=3, label=state_name,
        )
    ax_components.axvline(0, color=INK, lw=0.8)
    ax_components.set_yticks(base, list(comp_names.values()))
    ax_components.set_xlabel(r"Stress interaction ($10^{-4}$ h$^{-1}$ per SD)")
    ax_components.legend(frameon=False, loc="lower left")
    clean_axis(ax_components, "x")
    label_panel(ax_components, "a")

    subgroup = pd.read_csv(OUT / "differential_thermal_decay_subgroup_interactions.csv")
    regions = subgroup[(subgroup["subgroup_type"].eq("UN_SDG_region")) & subgroup["term"].eq("dhd_x_built_form_storage_score")].copy()
    region_short = {
        "Australia and New Zealand": "Australia & NZ",
        "Central and Southern Asia": "Central & Southern Asia",
        "Eastern and South-Eastern Asia": "Eastern & SE Asia",
        "Europe": "Europe",
        "Latin America and the Caribbean": "Latin America & Caribbean",
        "Northern Africa and Western Asia": "Northern Africa & Western Asia",
        "Northern America": "Northern America",
        "Sub-Saharan Africa": "Sub-Saharan Africa",
    }
    regions["label"] = regions["subgroup"].map(region_short)
    regions = regions.sort_values("estimate")
    yr = np.arange(len(regions))[::-1]
    ax_regions.errorbar(
        regions["estimate"], yr,
        xerr=[regions["estimate"] - regions["ci95_low"], regions["ci95_high"] - regions["estimate"]],
        fmt="o", color=GREEN, capsize=3,
    )
    ax_regions.axvline(0, color=INK, lw=0.8)
    ax_regions.set_yticks(yr, regions["label"])
    ax_regions.set_xlabel(r"DHD × storage proxy ($10^{-4}$ h$^{-1}$ SD$^{-1}$)")
    clean_axis(ax_regions, "x")
    label_panel(ax_regions, "b")

    period = subgroup[subgroup["subgroup_type"].eq("period")].copy()
    period["state"] = np.where(period["term"].str.startswith("extreme"), "Extreme DHD", "DHD")
    xp = np.arange(2)
    for state_name, color, marker, offset in [("DHD", ORANGE, "o", -0.08), ("Extreme DHD", RED, "s", 0.08)]:
        subset = period[period["state"].eq(state_name)].set_index("subgroup").loc[["2003-2013", "2014-2025"]]
        ax_period.errorbar(
            xp + offset, subset["estimate"],
            yerr=[subset["estimate"] - subset["ci95_low"], subset["ci95_high"] - subset["estimate"]],
            fmt=marker, color=color, capsize=3, label=state_name,
        )
    ax_period.axhline(0, color=INK, lw=0.8)
    ax_period.set_xticks(xp, ["2003–2013", "2014–2025"])
    ax_period.set_ylabel(r"Storage-proxy interaction ($10^{-4}$ h$^{-1}$ per SD)")
    ax_period.legend(frameon=False, loc="lower left")
    clean_axis(ax_period, "y")
    label_panel(ax_period, "c")

    coupled = pd.read_csv(OUT / "coupled_water_storage_interaction.csv")
    selected = coupled[coupled["term"].isin([
        "dhd_x_built_form_storage_score",
        "dhd_x_water_support",
        "dhd_x_storage_x_water_support",
    ])].copy()
    selected["label"] = selected["term"].map(
        {
            "dhd_x_built_form_storage_score": "DHD × built-form\nstorage proxy",
            "dhd_x_water_support": "DHD × water support",
            "dhd_x_storage_x_water_support": "DHD × storage ×\nwater support",
        }
    )
    yc = np.arange(len(selected))[::-1]
    ax_coupled.errorbar(
        selected["estimate"], yc,
        xerr=[selected["estimate"] - selected["ci95_low"], selected["ci95_high"] - selected["estimate"]],
        fmt="o", color=GREEN, capsize=3,
    )
    ax_coupled.axvline(0, color=INK, lw=0.8)
    ax_coupled.set_yticks(yc, selected["label"])
    ax_coupled.set_xlabel(r"Fixed-effect coefficient ($10^{-4}$ h$^{-1}$)")
    clean_axis(ax_coupled, "x")
    label_panel(ax_coupled, "d")
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.10, top=0.97)
    save(fig, "Figure_S3_component_regional_period_coupled_checks")


def supplementary_4() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.3, 2.75), gridspec_kw={"wspace": 0.52})
    ax_duration, ax_recovery, ax_tail = axes
    terms = pd.read_csv(OUT / "stress_memory_twfe_terms.csv")

    duration_models = [
        ("dhd_duration_differential_decay_1e4_h", "duration_excess_capped", "Differential decay", GREEN),
        ("dhd_duration_raw_night_contrast", "duration_excess_capped", "Raw nighttime contrast", BLUE),
        ("dhd_duration_inversion_0p25", "duration_excess_capped", "Severe inversion", RED),
    ]
    rows = []
    for model, term, label, color in duration_models:
        row = terms[(terms["model"].eq(model)) & terms["term"].eq(term)].iloc[0]
        rows.append({**row.to_dict(), "label": label, "color": color})
    duration = pd.DataFrame(rows)
    yd = np.arange(len(duration))[::-1]
    for i, row in duration.iterrows():
        ax_duration.errorbar(row["estimate"], yd[i], xerr=[[row["estimate"] - row["ci95_low"]], [row["ci95_high"] - row["estimate"]]], fmt="o", color=row["color"], capsize=3)
    ax_duration.axvline(0, color=INK, lw=0.8)
    ax_duration.set_yticks(yd, duration["label"])
    ax_duration.set_xlabel("Effect per additional DHD interval\n(outcome-specific units)")
    clean_axis(ax_duration, "x")
    label_panel(ax_duration, "a")

    recovery = terms[terms["model"].eq("post_dhd_memory_differential_decay_1e4_h")]
    recovery = recovery[recovery["term"].str.fullmatch(r"post_dhd_lag[1-4]")].copy()
    recovery["lag"] = recovery["term"].str.extract(r"(\d+)").astype(int)
    ax_recovery.errorbar(
        recovery["lag"] * 8, recovery["estimate"],
        yerr=[recovery["estimate"] - recovery["ci95_low"], recovery["ci95_high"] - recovery["estimate"]],
        marker="o", color=GREEN, capsize=3,
    )
    ax_recovery.axhline(0, color=INK, lw=0.8)
    ax_recovery.set_xticks([8, 16, 24, 32])
    ax_recovery.set_xlabel("Days after DHD ended")
    ax_recovery.set_ylabel(r"Differential-decay rebound ($10^{-4}$ h$^{-1}$)")
    clean_axis(ax_recovery, "y")
    label_panel(ax_recovery, "b")

    for threshold, color, marker in [(0.1, BLUE, "o"), (0.25, ORANGE, "s"), (0.5, RED, "^")]:
        label = str(threshold).replace(".", "p")
        subset = terms[terms["model"].eq(f"post_dhd_memory_inversion_{label}")]
        subset = subset[subset["term"].str.fullmatch(r"post_dhd_lag[1-4]")].copy()
        subset["lag"] = subset["term"].str.extract(r"(\d+)").astype(int)
        ax_tail.errorbar(
            subset["lag"] * 8, subset["estimate"],
            yerr=[subset["estimate"] - subset["ci95_low"], subset["ci95_high"] - subset["estimate"]],
            marker=marker, color=color, capsize=2, lw=1.2, label=f">{threshold:.2f} °C",
        )
    ax_tail.axhline(0, color=INK, lw=0.8)
    ax_tail.set_xticks([8, 16, 24, 32])
    ax_tail.set_xlabel("Days after DHD ended")
    ax_tail.set_ylabel("Excess inversion probability")
    ax_tail.legend(frameon=False, loc="upper right", fontsize=7)
    clean_axis(ax_tail, "y")
    label_panel(ax_tail, "c")
    save(fig, "Figure_S4_stress_duration_recovery_tail_memory")


def supplementary_5() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(9.0, 3.15), gridspec_kw={"wspace": 0.62})
    ax_null, ax_threshold, ax_counts = axes
    null = pd.read_csv(OUT / "severe_inversion_timing_null_summary.csv")
    null = null[null["statistic"].eq("max_population")].copy()
    null["label"] = null["null_name"].map(
        {
            "city-year circular shift": "City-year shift",
            "region-year block shift": "Region-year block",
            "DHD and true-night-heat timing preserved": "DHD + true-night heat\ntiming preserved",
        }
    )
    yn = np.arange(len(null))[::-1]
    ax_null.hlines(yn, null["null_ci95_low"] / 1e6, null["null_ci95_high"] / 1e6, color=GRAY, lw=3)
    ax_null.scatter(null["observed_slope"] / 1e6, yn, color=RED, s=32, zorder=3, label="Observed")
    ax_null.set_yticks(yn, null["label"])
    ax_null.set_xlabel("Annual maximum-population trend\n" + r"(million residents yr$^{-1}$)")
    ax_null.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.70, -0.25), fontsize=7.5)
    clean_axis(ax_null, "x")
    label_panel(ax_null, "a")

    summary = pd.read_csv(OUT / "corrected_inversion_concurrence_summary.csv")
    ax_threshold.bar(summary["inversion_threshold_c"].astype(str), summary["maximum_concurrent_represented_population"] / 1e6, color=[BLUE, GREEN, ORANGE, RED])
    ax_threshold.set_xlabel("Day/night inversion\nthreshold (°C)")
    ax_threshold.set_ylabel("Maximum concurrent represented\npopulation (million)")
    clean_axis(ax_threshold, "y")
    label_panel(ax_threshold, "b")

    thresholds = summary["inversion_threshold_c"].astype(str)
    x = np.arange(len(summary))
    width = 0.38
    ax_counts.bar(
        x - width / 2,
        summary["n_event_city_intervals"],
        width=width,
        color=GREEN,
        label="Event city-intervals",
    )
    ax_counts.bar(
        x + width / 2,
        summary["n_cities_ever"],
        width=width,
        color=GRAY,
        label="Cities ever",
    )
    ax_counts.set_xticks(x, thresholds)
    ax_counts.set_xlabel("Day/night inversion\nthreshold (°C)")
    ax_counts.set_ylabel("Count")
    ax_counts.legend(frameon=False, fontsize=6.8, loc="upper right")
    clean_axis(ax_counts, "y")
    label_panel(ax_counts, "c")
    fig.subplots_adjust(left=0.16, right=0.98, bottom=0.30, top=0.93, wspace=0.72)
    save(fig, "Figure_S5_timing_null_threshold_burden")


def main() -> None:
    setup()
    FIG.mkdir(parents=True, exist_ok=True)
    supplementary_1()
    supplementary_2()
    supplementary_3()
    supplementary_4()
    supplementary_5()
    print(f"Supplementary figures written to {FIG}")


if __name__ == "__main__":
    main()
