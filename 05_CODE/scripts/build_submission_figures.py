#!/usr/bin/env python3
"""Build deterministic submission Figures 1 and 4 from frozen evidence.

The script reads package-local, source-traceable CSV evidence. It does not read
or modify manuscript prose and does not fit any model or resample any data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "02_EVIDENCE"
FIGURES = ROOT / "03_FIGURES"

SOURCES = {
    "chronology": EVIDENCE / "si_tables" / "fixed_interval_chronology.csv",
    "cohorts": EVIDENCE / "si_tables" / "cohort_attrition_summary.csv",
    "actions": EVIDENCE / "tables" / "metric_aware_decision_audit.csv",
    "external_points": EVIDENCE
    / "external_replication"
    / "validation_2021_exact_mse_budget.csv",
    "external_bootstrap": EVIDENCE
    / "external_replication"
    / "validation_2021_bootstrap_summary.csv",
    "external_events": EVIDENCE
    / "external_replication"
    / "validation_2021_event_influence.csv",
    "external_intervals": EVIDENCE
    / "external_replication"
    / "design_inputs"
    / "goes_sunset_intervals.csv",
    "mse_points": EVIDENCE / "tables" / "exact_mse_budgets_with_external.csv",
    "mse_bootstrap": EVIDENCE / "tables" / "mse_budget_2026_bootstrap_summary.csv",
    "uncertainty_gate": EVIDENCE
    / "si_tables"
    / "uncertainty_gate_2026_by_cohort_event.csv",
}

# Okabe-Ito palette plus neutral tones.
COLORS = {
    "core": "#0072B2",
    "ring": "#E69F00",
    "contrast": "#009E73",
    "calibration": "#56B4E9",
    "evaluation": "#009E73",
    "historical": "#E69F00",
    "prospective": "#CC79A7",
    "variance": "#0072B2",
    "bias": "#009E73",
    "covariance": "#D55E00",
    "net": "#303030",
    "ink": "#202020",
    "muted": "#666666",
    "grid": "#D9D9D9",
    "panel": "#F7F7F7",
}

FIXED_EXPORT_TIME = datetime(2026, 8, 12, tzinfo=timezone.utc)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.0,
            "axes.labelsize": 8.5,
            "axes.titlesize": 9.0,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.0,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "gsis-submission-figures-v1",
        }
    )


def read_sources() -> dict[str, pd.DataFrame]:
    for label, path in SOURCES.items():
        require(path.exists(), f"Missing {label} source: {path}")
    return {label: pd.read_csv(path) for label, path in SOURCES.items()}


def validate_sources(data: dict[str, pd.DataFrame]) -> dict[str, object]:
    chronology = data["chronology"].copy()
    chronology["start_date"] = pd.to_datetime(chronology["start_date"])
    chronology["end_date"] = pd.to_datetime(chronology["end_date"])
    require(len(chronology) == 57, "Expected 57 fixed design intervals")
    require(
        chronology["year"].min() == 2019 and chronology["year"].max() == 2026,
        "Chronology must span study data years 2019–2026",
    )
    require(
        chronology["interval_days_inclusive"].eq(8).all(),
        "All fixed intervals must contain eight inclusive dates",
    )
    expected_design_rows = {
        "goes17_goes16_2019_2021": 8,
        "goes18_goes16_2022_2024": 31,
        "goes18_goes19_2025": 10,
        "goes18_goes19_2026": 8,
    }
    require(
        chronology["design_id"].value_counts().to_dict() == expected_design_rows,
        "Fixed chronology design counts changed",
    )

    cohorts = data["cohorts"].set_index("stage_id")
    expected_cohort_counts = {
        "external_calibration_combined_2019_2020": (69, 4, 2533, np.nan),
        "external_validation_combined_2021": (69, 4, 2571, 246),
        "initial_model_derivation_original_2022_2024": (44, 31, 13454, 1352),
        "initial_model_evaluation_expansion_2022_2024": (31, 31, 9197, 886),
        "initial_model_evaluation_original_2025": (44, 10, 4180, 435),
        "initial_model_evaluation_expansion_2025": (31, 10, 2963, 298),
        "metric_aware_calibration_combined_2025": (75, 10, 7143, 733),
        "metric_aware_validation_combined_2026": (75, 8, 5744, 588),
    }
    require(set(cohorts.index) == set(expected_cohort_counts), "Cohort stages changed")
    for stage, (cities, events, hourly, transitions) in expected_cohort_counts.items():
        row = cohorts.loc[stage]
        require(int(row["analyzed_cities"]) == cities, f"City count changed: {stage}")
        require(int(row["fixed_intervals"]) == events, f"Event count changed: {stage}")
        require(
            int(row["hourly_city_event_rows"]) == hourly,
            f"Hourly count changed: {stage}",
        )
        if not np.isnan(transitions):
            require(
                int(row["eligible_transition_city_events"]) == transitions,
                f"Transition count changed: {stage}",
            )

    actions = data["actions"]
    action_lookup = actions.set_index("measurement_level")["operational_action"].to_dict()
    require(
        action_lookup["spatial contrast"] == "retain raw downstream metric"
        and action_lookup["temporal transition"] == "retain raw downstream metric"
        and action_lookup["directional inference"] == "certify or abstain",
        "Frozen downstream actions changed",
    )
    require(
        actions.loc[actions["measurement_level"].eq("component"), "operational_action"]
        .eq("use component correction")
        .all(),
        "Frozen component action changed",
    )

    external_points = data["external_points"]
    external_point = external_points[external_points["scope"].eq("hourly")].iloc[0]
    for component in ["core", "ring", "anomaly"]:
        reconstructed = 1.0 - (
            external_point[f"harm_{component}_rmse_k"]
            / external_point[f"raw_{component}_rmse_k"]
        )
        require(
            abs(reconstructed - external_point[f"{component}_rmse_reduction_fraction"])
            < 1e-12,
            f"External {component} RMSE reduction does not reconstruct",
        )

    external_bootstrap = data["external_bootstrap"]
    external_ci = external_bootstrap[
        external_bootstrap["scope"].eq("hourly")
        & external_bootstrap["metric"].isin(
            [
                "core_rmse_reduction_fraction",
                "ring_rmse_reduction_fraction",
                "anomaly_rmse_reduction_fraction",
            ]
        )
    ].set_index("metric")
    require(len(external_ci) == 3, "Missing 2021 RMSE bootstrap intervals")
    require(external_ci["n_bootstrap"].eq(5000).all(), "2021 bootstrap is not 5,000 draws")
    for component in ["core", "ring", "anomaly"]:
        point = external_point[f"{component}_rmse_reduction_fraction"]
        row = external_ci.loc[f"{component}_rmse_reduction_fraction"]
        require(row["ci95_low"] <= point <= row["ci95_high"], f"2021 {component} point is outside its interval")

    intervals = data["external_intervals"].rename(columns={"time_id": "event_time_id"})
    events = data["external_events"]
    single_events = events[events["diagnostic"].eq("single_event")].merge(
        intervals[["event_time_id", "start_date", "analysis_role"]],
        on="event_time_id",
        how="left",
        validate="one_to_one",
    )
    require(len(single_events) == 4, "Expected four external validation events")
    require(single_events["analysis_role"].eq("validation").all(), "Event/date mapping failed")
    require(
        (
            single_events[
                ["core_rmse_reduction_fraction", "ring_rmse_reduction_fraction"]
            ]
            > 0
        )
        .all()
        .all(),
        "A 2021 event lacks component improvement",
    )

    mse_points = data["mse_points"]
    mse_point = mse_points[
        mse_points["sample"].eq("2026 combined GOES18/19")
        & mse_points["scope"].eq("hourly")
    ].iloc[0]
    point_closure = (
        mse_point["component_variance_gain_k2"]
        + mse_point["differential_bias_gain_k2"]
        - mse_point["covariance_loss_penalty_k2"]
        - mse_point["net_downstream_mse_gain_k2"]
    )
    require(abs(point_closure) < 1e-12, "2026 observed MSE budget does not close")

    mse_bootstrap = data["mse_bootstrap"]
    mse_ci = mse_bootstrap[
        mse_bootstrap["scope"].eq("hourly")
        & mse_bootstrap["metric"].isin(
            [
                "component_variance_gain_k2",
                "differential_bias_gain_k2",
                "covariance_loss_penalty_k2",
                "net_downstream_mse_gain_k2",
            ]
        )
    ].set_index("metric")
    require(len(mse_ci) == 4, "Missing 2026 hourly MSE-budget intervals")
    require(mse_ci["n_bootstrap"].eq(5000).all(), "2026 bootstrap is not 5,000 draws")
    require(
        mse_ci.loc["net_downstream_mse_gain_k2", "ci95_low"] < 0
        < mse_ci.loc["net_downstream_mse_gain_k2", "ci95_high"],
        "2026 net-gain interval should span zero",
    )

    gate = data["uncertainty_gate"]
    gate = gate[gate["scope_type"].eq("cohort")].set_index("scope_label")
    require(set(gate.index) == {"combined", "original", "expansion"}, "Gate cohorts changed")
    for label, row in gate.iterrows():
        require(
            abs(row["coverage"] - row["n_covered"] / row["n_transitions"]) < 1e-12,
            f"Coverage count mismatch: {label}",
        )
        require(
            abs(
                row["certified_fraction"]
                - row["n_certified"] / row["n_transitions"]
            )
            < 1e-12,
            f"Certification count mismatch: {label}",
        )
        require(
            abs(
                row["certified_sign_accuracy"]
                - row["n_certified_correct"] / row["n_certified"]
            )
            < 1e-12,
            f"Certified GOES-18 sign-agreement count mismatch: {label}",
        )
    require(
        int(gate.loc["combined", "n_transitions"])
        == int(gate.loc["original", "n_transitions"])
        + int(gate.loc["expansion", "n_transitions"]),
        "Original and expansion transition counts do not sum to combined",
    )
    require(
        bool(gate.loc["combined", "formal_gate_scope"])
        and not bool(gate.loc["original", "formal_gate_scope"])
        and not bool(gate.loc["expansion", "formal_gate_scope"]),
        "Formal versus diagnostic gate scopes changed",
    )

    data["external_point"] = pd.DataFrame([external_point])
    data["external_ci"] = external_ci.reset_index()
    data["single_events"] = single_events.sort_values("start_date")
    data["mse_point"] = pd.DataFrame([mse_point])
    data["mse_ci"] = mse_ci.reset_index()
    data["gate_cohorts"] = gate.reset_index()

    return {
        "status": "all_source_checks_passed",
        "chronology_rows": int(len(chronology)),
        "cohort_stages": int(len(cohorts)),
        "external_2021_hourly_n": int(external_point["n"]),
        "external_2021_events": int(len(single_events)),
        "bootstrap_draws_per_scope": 5000,
        "holdout_2026_hourly_n": int(mse_point["n"]),
        "gate_2026_transition_n": int(gate.loc["combined", "n_transitions"]),
        "maximum_point_budget_closure_residual_k2": float(abs(point_closure)),
    }


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    facecolor: str,
    edgecolor: str,
    text: str,
    textcolor: str = COLORS["ink"],
    fontsize: float = 7.0,
    linewidth: float = 1.0,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        transform=ax.transAxes,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=textcolor,
        fontsize=fontsize,
        linespacing=1.2,
    )


def axes_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str = COLORS["muted"],
    mutation_scale: float = 9,
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        transform=ax.transAxes,
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        linewidth=0.9,
        color=color,
        shrinkA=1,
        shrinkB=1,
    )
    ax.add_patch(arrow)


def timeline_block(
    ax: plt.Axes,
    start: float,
    end: float,
    y: float,
    height: float,
    facecolor: str,
    text: str,
    textcolor: str = COLORS["ink"],
    edgecolor: str = "none",
    hatch: str | None = None,
    fontsize: float = 6.2,
) -> None:
    rect = Rectangle(
        (start, y),
        end - start,
        height,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=0,
        hatch=hatch,
        zorder=2,
    )
    ax.add_patch(rect)
    ax.text(
        (start + end) / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        color=textcolor,
        fontsize=fontsize,
        linespacing=1.12,
        zorder=3,
    )


def build_figure1(data: dict[str, pd.DataFrame]) -> plt.Figure:
    # Give the hierarchy its own full-width axes. Sharing a constrained-layout
    # column with the timeline previously reserved the timeline's wide y-label
    # margin above panel a, compressing the hierarchy and clipping the padded
    # edge of its first rounded box.
    fig = plt.figure(figsize=(7.8, 5.25))
    hierarchy = fig.add_axes([0.035, 0.625, 0.945, 0.335])
    timeline = fig.add_axes([0.205, 0.075, 0.765, 0.445])

    hierarchy.set_axis_off()
    # Panel labels share an absolute left margin even though the chronology
    # axes reserve additional space for its long row labels.
    fig.text(0.015, 0.975, "a", ha="left", va="top", fontsize=11, fontweight="bold")
    fig.text(0.015, 0.545, "b", ha="left", va="top", fontsize=11, fontweight="bold")
    hierarchy.text(
        0.01,
        0.90,
        "Scientific measurands",
        transform=hierarchy.transAxes,
        color=COLORS["muted"],
        fontsize=6.2,
        fontweight="bold",
    )
    hierarchy.text(
        0.245,
        0.39,
        "Measurand-level actions",
        transform=hierarchy.transAxes,
        color=COLORS["muted"],
        fontsize=6.2,
        fontweight="bold",
        ha="center",
    )

    # Narrow all eight boxes uniformly to give each horizontal derivation
    # arrow and its label an unambiguous gap between neighboring boxes.
    box_x = [0.02, 0.27, 0.52, 0.77]
    box_width = 0.17
    measurands = [
        ("Component LST\n$C$ urban core\n$R$ surrounding ring", "#EAF4FA", COLORS["core"]),
        ("Spatial contrast\n$D = C - R$", "#EAF7F2", COLORS["contrast"]),
        (
            r"Temporal transition" "\n" r"$T = D_{\mathrm{post}} - D_{\mathrm{pre}}$",
            "#F3EDF5",
            COLORS["prospective"],
        ),
        ("Transition direction\n$\\operatorname{sign}(T)$", "#F3EDF5", COLORS["prospective"]),
    ]
    actions = [
        ("Selected component models\nUse component correction", "#DDEFF7", COLORS["core"]),
        ("Raw selected\nRetain raw contrast", "#DDF1EA", COLORS["contrast"]),
        ("Raw selected\nRetain raw transition", "#F0E2EF", COLORS["prospective"]),
        (
            "Empirical residual interval\nSupport sign or abstain",
            "#F0E2EF",
            COLORS["prospective"],
        ),
    ]
    for x, (text, fill, edge), (action, action_fill, action_edge) in zip(
        box_x, measurands, actions
    ):
        rounded_box(
            hierarchy,
            x,
            0.59,
            box_width,
            0.24,
            fill,
            edge,
            text,
            fontsize=6.5,
        )
        rounded_box(
            hierarchy,
            x,
            0.025,
            box_width,
            0.205,
            action_fill,
            action_edge,
            action,
            fontsize=5.8,
        )
        axes_arrow(
            hierarchy,
            (x + box_width / 2, 0.585),
            (x + box_width / 2, 0.235),
        )

    for left, right in zip(box_x[:-1], box_x[1:]):
        axes_arrow(
            hierarchy,
            (left + box_width + 0.022, 0.70),
            (right - 0.022, 0.70),
        )
        hierarchy.text(
            (left + box_width + right) / 2,
            0.735,
            "derive",
            transform=hierarchy.transAxes,
            ha="center",
            va="bottom",
            color=COLORS["muted"],
            fontsize=5.8,
        )

    timeline.set_xlim(2018.85, 2026.95)
    timeline.set_ylim(0.34, 3.55)
    timeline.set_yticks(
        [3.00, 1.96, 0.81],
        [
            "External replication\nGOES-17 / GOES-16",
            "Initial transfer\nGOES-18/16 → GOES-18/19",
            "Measurand-aware test\nGOES-18 / GOES-19",
        ],
    )
    timeline.set_xticks(np.arange(2019, 2027))
    timeline.set_xticklabels([str(year) for year in range(2019, 2027)])
    timeline.grid(False)
    timeline.spines[["right", "top"]].set_visible(False)
    timeline.spines["left"].set_visible(True)
    timeline.spines["left"].set_color(COLORS["muted"])
    timeline.spines["bottom"].set_color(COLORS["muted"])
    timeline.tick_params(axis="x", length=3, color=COLORS["muted"])
    timeline.tick_params(
        axis="y",
        length=3,
        width=0.7,
        color=COLORS["muted"],
        pad=5,
        labelsize=6.0,
    )
    for label in timeline.get_yticklabels():
        label.set_horizontalalignment("right")
        label.set_fontweight("bold")
    timeline_block(
        timeline,
        2019.20,
        2020.60,
        2.76,
        0.48,
        COLORS["calibration"],
        "Calibration\n69 c | 4 e",
        fontsize=6.0,
    )
    timeline_block(
        timeline,
        2021.17,
        2021.79,
        2.76,
        0.48,
        COLORS["historical"],
        "Hist. eval.\n69 c | 4 e",
        fontsize=5.7,
    )
    timeline.annotate(
        "",
        xy=(2021.10, 3.00),
        xytext=(2020.67, 3.00),
        arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": COLORS["muted"]},
    )

    timeline_block(
        timeline,
        2022.23,
        2024.58,
        2.00,
        0.31,
        COLORS["calibration"],
        "Original derivation\n44 c | 31 e",
        fontsize=5.6,
    )
    timeline_block(
        timeline,
        2022.23,
        2024.58,
        1.62,
        0.31,
        COLORS["evaluation"],
        "Expansion evaluation\n31 c | 31 e",
        fontsize=5.6,
    )
    timeline_block(
        timeline,
        2025.15,
        2025.77,
        1.62,
        0.69,
        COLORS["evaluation"],
        "OOS evaluation\n75 c | 10 e",
        fontsize=5.6,
    )
    timeline.annotate(
        "",
        xy=(2025.08, 1.96),
        xytext=(2024.65, 1.96),
        arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": COLORS["muted"]},
    )

    timeline_block(
        timeline,
        2025.16,
        2025.76,
        0.56,
        0.50,
        COLORS["calibration"],
        "Calibration\n75 c | 10 e",
        fontsize=5.6,
    )
    timeline_block(
        timeline,
        2026.22,
        2026.82,
        0.56,
        0.50,
        COLORS["prospective"],
        "Holdout\n75 c | 8 e",
        fontsize=5.6,
    )
    timeline.annotate(
        "",
        xy=(2026.15, 0.81),
        xytext=(2025.83, 0.81),
        arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": COLORS["muted"]},
    )

    legend = [
        Patch(facecolor=COLORS["calibration"], edgecolor="none", label="Calibration / derivation"),
        Patch(facecolor=COLORS["evaluation"], edgecolor="none", label="Out-of-sample evaluation"),
        Patch(facecolor=COLORS["historical"], edgecolor="none", label="Historical external evaluation"),
        Patch(facecolor=COLORS["prospective"], edgecolor="none", label="Prospective holdout"),
    ]
    timeline.legend(
        handles=legend,
        loc="upper left",
        bbox_to_anchor=(0.0, 1.01),
        frameon=False,
        ncol=4,
        handlelength=1.3,
        columnspacing=1.0,
        borderaxespad=0,
        fontsize=5.8,
    )
    timeline.annotate(
        "",
        xy=(2025.48, 1.07),
        xytext=(2025.48, 1.61),
        arrowprops={"arrowstyle": "-|>", "lw": 0.7, "color": COLORS["muted"]},
    )
    timeline.text(
        2025.37,
        1.34,
        "also calibration\nsource",
        ha="right",
        va="center",
        fontsize=5.1,
        color=COLORS["muted"],
    )
    return fig


def clean_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.7)


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.11,
        1.12,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
    )


def component_legend_handles() -> list[Line2D]:
    return [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor=color,
            markeredgecolor="none",
            markersize=5,
            label=label,
        )
        for label, color in zip(
            ["Core", "Ring", "Core−ring contrast"],
            [COLORS["core"], COLORS["ring"], COLORS["contrast"]],
        )
    ]


def build_figure4(data: dict[str, pd.DataFrame]) -> plt.Figure:
    fig, axes = plt.subplots(2, 2, figsize=(7.6, 6.2), constrained_layout=True)
    ax_a, ax_b, ax_c, ax_d = axes.ravel()

    external_point = data["external_point"].iloc[0]
    external_ci = data["external_ci"].set_index("metric")
    components = ["core", "ring", "anomaly"]
    labels = ["Core", "Ring", "Core−ring contrast"]
    colors = [COLORS["core"], COLORS["ring"], COLORS["contrast"]]
    # Compact the category spacing and reserve explicit clearance below the
    # lowest point for its downward/right numerical label.
    y = np.array([0.0, 0.72, 1.44])
    point_pct = np.array(
        [external_point[f"{component}_rmse_reduction_fraction"] for component in components]
    ) * 100
    low_pct = np.array(
        [external_ci.loc[f"{component}_rmse_reduction_fraction", "ci95_low"] for component in components]
    ) * 100
    high_pct = np.array(
        [external_ci.loc[f"{component}_rmse_reduction_fraction", "ci95_high"] for component in components]
    ) * 100
    for yi, point, low, high, color in zip(y, point_pct, low_pct, high_pct, colors):
        ax_a.errorbar(
            point,
            yi,
            xerr=np.array([[point - low], [high - point]]),
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=1.6,
            capsize=3.5,
            markersize=5.5,
            markeredgecolor="none",
            markeredgewidth=0,
            zorder=3,
        )
        ax_a.annotate(
            f"{point:.1f}%",
            (point, yi),
            xytext=(5, -9),
            textcoords="offset points",
            ha="left",
            va="top",
            fontsize=6.8,
        )
    ax_a.axvline(0, color=COLORS["ink"], linewidth=0.8)
    ax_a.set_yticks(y, labels)
    ax_a.set_ylim(1.90, -0.25)
    ax_a.set_xlim(-10, 68)
    ax_a.set_xlabel("Observed RMSE reduction (%)")
    panel_label(ax_a, "a")
    clean_axis(ax_a)

    events = data["single_events"].copy()
    events["start_date"] = pd.to_datetime(events["start_date"])
    base_y = np.arange(len(events))
    offsets = {"core": -0.20, "ring": 0.0, "anomaly": 0.20}
    for component, color, label in zip(components, colors, labels):
        values = events[f"{component}_rmse_reduction_fraction"].to_numpy() * 100
        ax_b.scatter(
            values,
            base_y + offsets[component],
            s=27,
            color=color,
            edgecolor="none",
            linewidth=0,
            label=label,
            zorder=3,
        )
    ax_b.axvline(0, color=COLORS["ink"], linewidth=0.8)
    event_labels = [
        f"{date.strftime('%-d %b')}  (n={int(n):,})"
        for date, n in zip(events["start_date"], events["n"])
    ]
    ax_b.set_yticks(base_y, event_labels)
    ax_b.invert_yaxis()
    ax_b.set_xlim(0, 64)
    ax_b.margins(x=0)
    ax_b.set_xlabel("Event-specific RMSE reduction (%)")
    ax_b.legend(
        handles=component_legend_handles(),
        loc="upper right",
        bbox_to_anchor=(1.0, 1.08),
        frameon=False,
        ncol=3,
        borderaxespad=0,
        handletextpad=0.3,
        columnspacing=0.8,
        fontsize=6.2,
    )
    panel_label(ax_b, "b")
    clean_axis(ax_b)

    mse_point = data["mse_point"].iloc[0]
    mse_ci = data["mse_ci"].set_index("metric")
    metric_names = [
        "component_variance_gain_k2",
        "differential_bias_gain_k2",
        "covariance_loss_penalty_k2",
        "net_downstream_mse_gain_k2",
    ]
    term_labels = [
        "Component-variance gain",
        "Differential-bias gain",
        "Covariance-loss penalty",
        "Net downstream gain",
    ]
    term_colors = [COLORS["variance"], COLORS["bias"], COLORS["covariance"], COLORS["net"]]
    points = np.array(
        [
            mse_point["component_variance_gain_k2"],
            mse_point["differential_bias_gain_k2"],
            -mse_point["covariance_loss_penalty_k2"],
            mse_point["net_downstream_mse_gain_k2"],
        ]
    )
    lows = np.array(
        [
            mse_ci.loc[metric_names[0], "ci95_low"],
            mse_ci.loc[metric_names[1], "ci95_low"],
            -mse_ci.loc[metric_names[2], "ci95_high"],
            mse_ci.loc[metric_names[3], "ci95_low"],
        ]
    )
    highs = np.array(
        [
            mse_ci.loc[metric_names[0], "ci95_high"],
            mse_ci.loc[metric_names[1], "ci95_high"],
            -mse_ci.loc[metric_names[2], "ci95_low"],
            mse_ci.loc[metric_names[3], "ci95_high"],
        ]
    )
    # Compact term spacing and leave additional lower clearance for the net
    # downstream-gain value label.
    term_y = np.array([0.0, 0.60, 1.20, 1.80])
    for yi, point, low, high, color, metric_name in zip(
        term_y, points, lows, highs, term_colors, metric_names
    ):
        marker_size = 3.4 if metric_name == "net_downstream_mse_gain_k2" else 5.0
        ax_c.errorbar(
            point,
            yi,
            xerr=np.array([[point - low], [high - point]]),
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=1.6,
            capsize=3.5,
            markersize=marker_size,
            markeredgecolor="none",
            markeredgewidth=0,
            zorder=3,
        )
        ax_c.annotate(
            f"{point:+.3f}".replace("-", "−"),
            (point, yi),
            xytext=(5, -9),
            textcoords="offset points",
            ha="left",
            va="top",
            fontsize=6.7,
        )
    ax_c.axvline(0, color=COLORS["ink"], linewidth=0.8)
    ax_c.set_yticks(term_y, term_labels)
    ax_c.set_ylim(2.28, -0.25)
    ax_c.set_xlim(-2.25, 2.40)
    ax_c.set_xlabel("Observed contribution to MSE gain (K²)")
    panel_label(ax_c, "c")
    clean_axis(ax_c)

    gate = data["gate_cohorts"].set_index("scope_label").loc[
        ["combined", "original", "expansion"]
    ]
    cohort_labels = [
        "Combined\nformal\nn=588",
        "Original\ndiagnostic\nn=349",
        "Expansion\ndiagnostic\nn=239",
    ]
    gate_metrics = ["coverage", "certified_fraction", "certified_sign_accuracy"]
    gate_labels = ["Coverage", "Sign supported", "G18 sign agreement"]
    gate_colors = [COLORS["core"], COLORS["ring"], COLORS["contrast"]]
    x = np.arange(3)
    width = 0.24
    for index, (metric, label, color) in enumerate(zip(gate_metrics, gate_labels, gate_colors)):
        values = gate[metric].to_numpy() * 100
        positions = x + (index - 1) * width
        bars = ax_d.bar(
            positions,
            values,
            width=width * 0.92,
            color=color,
            edgecolor="none",
            linewidth=0,
            label=label,
            zorder=2,
        )
        for cohort_index, (bar, value) in enumerate(zip(bars, values)):
            row = gate.iloc[cohort_index]
            if metric == "coverage":
                fraction = f"{int(row['n_covered'])}/{int(row['n_transitions'])}"
            elif metric == "certified_fraction":
                fraction = f"{int(row['n_certified'])}/{int(row['n_transitions'])}"
            else:
                fraction = f"{int(row['n_certified_correct'])}/{int(row['n_certified'])}"
            ax_d.text(
                bar.get_x() + bar.get_width() / 2,
                value + 1.2,
                f"{value:.1f}",
                ha="center",
                va="bottom",
                fontsize=5.8,
            )
            ax_d.text(
                bar.get_x() + bar.get_width() / 2,
                max(2.0, min(value * 0.48, value - 5.0)),
                fraction,
                ha="center",
                va="center",
                rotation=90,
                fontsize=5.5,
                color=COLORS["ink"],
                fontweight="bold",
            )
    ax_d.set_xticks(x, cohort_labels)
    ax_d.set_ylim(0, 120)
    ax_d.set_yticks(np.arange(0, 121, 20))
    ax_d.margins(y=0)
    ax_d.set_ylabel("Held-out transitions (%)")
    ax_d.legend(
        loc="upper right",
        bbox_to_anchor=(1.0, 1.08),
        frameon=False,
        ncol=3,
        columnspacing=0.8,
        handlelength=1.1,
        fontsize=6.0,
        borderaxespad=0,
    )
    panel_label(ax_d, "d")
    clean_axis(ax_d)
    return fig


def export_figure(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for extension in ["png", "pdf", "svg"]:
        path = FIGURES / f"{stem}.{extension}"
        if extension == "pdf":
            metadata = {
                "Creator": "build_submission_figures.py",
                "CreationDate": FIXED_EXPORT_TIME,
                "ModDate": FIXED_EXPORT_TIME,
            }
        elif extension == "svg":
            metadata = {
                "Creator": "build_submission_figures.py",
                "Date": "2026-08-12",
            }
        else:
            metadata = {"Software": "build_submission_figures.py"}
        fig.savefig(
            path,
            dpi=400 if extension == "png" else None,
            bbox_inches="tight",
            facecolor="white",
            metadata=metadata,
        )
        if extension == "svg":
            svg_text = path.read_text(encoding="utf-8")
            path.write_text(
                "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
                encoding="utf-8",
            )
    plt.close(fig)


def write_captions() -> None:
    figure1 = r"""**Figure 1. Measurand-aware cross-platform harmonization workflow and evaluation chronology.** **(a)** The measurement hierarchy proceeds from urban-core and surrounding-ring land surface temperature (LST) components to the core-minus-ring spatial contrast and the pre-to-post-sunset transition, \(T=D_{\mathrm{post}}-D_{\mathrm{pre}}\). Out-of-sample loss supports correction or raw retention at each measurement level; a separate empirically calibrated residual interval supports a positive or negative transition sign when it excludes zero and otherwise abstains. **(b)** Calibration and evaluation stages across GOES-17/16, GOES-18/16, and GOES-18/19, where the first platform is the inter-platform consistency reference and the second is the mapped source. The 2021 stage is an outcome-blind historical external replication; models and actions for the prospective 2026 holdout were prespecified from 2025 calibration.
"""
    figure4 = """**Figure 4. Historical external replication and prospective holdout diagnostics.** **(a)** Observed 2021 hourly root-mean-squared error (RMSE) reductions for urban-core, surrounding-ring, and core–ring contrast; bars are 95% crossed city–event bootstrap intervals from 5,000 draws. The external evaluation contained 2,571 records from 69 cities and four fixed events. **(b)** Observed event-specific reductions; labels give interval start date and retained record count, and no event-specific uncertainty interval is implied. **(c)** Observed prospective 2026 hourly mean-squared-error (MSE) decomposition terms with 95% crossed-bootstrap intervals; the net-gain interval spans zero. The covariance-loss penalty is plotted on the negative x-axis because it subtracts from downstream MSE gain. **(d)** Coverage, fraction for which the interval excluded zero, and agreement of supported signs with the GOES-18 reference-platform sign. The pooled combined holdout was the formal prespecified decision scope; original and expansion rows are transport diagnostics.
"""
    (FIGURES / "figure1_workflow_timeline_caption.md").write_text(
        figure1, encoding="utf-8"
    )
    (FIGURES / "figure4_replication_holdout_diagnostics_caption.md").write_text(
        figure4, encoding="utf-8"
    )


def main() -> None:
    configure_style()
    data = read_sources()
    validation = validate_sources(data)
    export_figure(build_figure1(data), "figure1_workflow_timeline")
    export_figure(build_figure4(data), "figure4_replication_holdout_diagnostics")
    write_captions()
    output_files = sorted(
        [
            f"03_FIGURES/figure1_workflow_timeline.{extension}"
            for extension in ["png", "pdf", "svg"]
        ]
        + [
            f"03_FIGURES/figure4_replication_holdout_diagnostics.{extension}"
            for extension in ["png", "pdf", "svg"]
        ]
        + [
            "03_FIGURES/figure1_workflow_timeline_caption.md",
            "03_FIGURES/figure4_replication_holdout_diagnostics_caption.md",
        ]
    )
    print(
        json.dumps(
            {
                **validation,
                "sources": {label: str(path.relative_to(ROOT)) for label, path in SOURCES.items()},
                "outputs": output_files,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
