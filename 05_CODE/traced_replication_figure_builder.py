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

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

EVIDENCE = ROOT / "02_EVIDENCE"

FIGURES = (
    ROOT
    / "07_SUBMISSION"
    / "Remote_Sensing_Main_Figures_600dpi_Font_Enlarged_v3"
)

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

FIXED_EXPORT_TIME = datetime(2026, 10, 29, tzinfo=timezone.utc)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            # Figures are drawn at their final 6.879-inch manuscript width,
            # so these values are the effective publication sizes rather than
            # sizes that will later be reduced by Word.
            "font.size": 8.5,
            "axes.labelsize": 9.5,
            "axes.titlesize": 10.0,
            "xtick.labelsize": 8.2,
            "ytick.labelsize": 8.2,
            "legend.fontsize": 8.0,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "gsis-submission-figures-v1",
        }
    )

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
        linespacing=1.1,
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
    text_x: float | None = None,
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
        (start + end) / 2 if text_x is None else text_x,
        y + height / 2,
        text,
        ha="center",
        va="center",
        color=textcolor,
        fontsize=fontsize,
        fontstretch="condensed",
        linespacing=1.12,
        zorder=3,
    )

def build_figure1(data: dict[str, pd.DataFrame]) -> plt.Figure:
    # Give the hierarchy its own full-width axes. Sharing a constrained-layout
    # column with the timeline previously reserved the timeline's wide y-label
    # margin above panel a, compressing the hierarchy and clipping the padded
    # edge of its first rounded box.
    fig = plt.figure(figsize=(6.879, 6.10))
    hierarchy = fig.add_axes([0.035, 0.655, 0.945, 0.315])
    timeline = fig.add_axes([0.200, 0.065, 0.770, 0.420])

    hierarchy.set_axis_off()
    # Panel labels share an absolute left margin even though the chronology
    # axes reserve additional space for its long row labels.
    fig.text(0.012, 0.978, "a", ha="left", va="top", fontsize=12, fontweight="bold")
    fig.text(0.012, 0.570, "b", ha="left", va="top", fontsize=12, fontweight="bold")
    hierarchy.text(
        0.01,
        0.935,
        "Scientific measurands",
        transform=hierarchy.transAxes,
        color=COLORS["muted"],
        fontsize=9.0,
        fontweight="bold",
    )
    hierarchy.text(
        0.01,
        -0.055,
        "Measurand-level actions",
        transform=hierarchy.transAxes,
        color=COLORS["muted"],
        fontsize=9.0,
        fontweight="bold",
        ha="left",
        va="top",
        clip_on=False,
    )

    # Narrow all eight boxes uniformly to give each horizontal derivation
    # arrow and its label an unambiguous gap between neighboring boxes.
    box_x = [0.015, 0.273, 0.531, 0.789]
    box_width = 0.178
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
        ("Selected component\nmodels\nUse component\ncorrection", "#DDEFF7", COLORS["core"]),
        ("Raw selected\nRetain raw contrast", "#DDF1EA", COLORS["contrast"]),
        ("Raw selected\nRetain raw transition", "#F0E2EF", COLORS["prospective"]),
        (
            "Empirical residual\ninterval\nSupport sign\nor abstain",
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
            0.545,
            box_width,
            0.255,
            fill,
            edge,
            text,
            fontsize=8.3,
        )
        rounded_box(
            hierarchy,
            x,
            0.025,
            box_width,
            0.275,
            action_fill,
            action_edge,
            action,
            fontsize=8.0,
        )
        axes_arrow(
            hierarchy,
            (x + box_width / 2, 0.540),
            (x + box_width / 2, 0.305),
        )

    for left, right in zip(box_x[:-1], box_x[1:]):
        axes_arrow(
            hierarchy,
            (left + box_width + 0.007, 0.665),
            (right - 0.007, 0.665),
        )
        hierarchy.text(
            (left + box_width + right) / 2,
            0.815,
            "derive",
            transform=hierarchy.transAxes,
            ha="center",
            va="bottom",
            color=COLORS["muted"],
            fontsize=8.0,
        )

    # Treat each displayed year as a full calendar-year cell. Phase boundaries
    # therefore fall on integer x coordinates while year labels sit at the
    # corresponding cell centers. The bars identify study phases, not
    # continuous satellite-observation coverage.
    timeline.set_xlim(2019, 2027)
    timeline.set_ylim(0.34, 3.55)
    timeline.set_yticks(
        [3.00, 1.96, 0.81],
        [
            "External\nreplication\nGOES-17 / GOES-16",
            "Initial transfer\nGOES-18/16 →\nGOES-18/19",
            "Measurand-aware\ntest\nGOES-18 / GOES-19",
        ],
    )
    timeline.set_xticks(np.arange(2019.5, 2027.5))
    timeline.set_xticklabels([str(year) for year in range(2019, 2027)])
    timeline.set_xticks(np.arange(2019, 2028), minor=True)
    timeline.grid(False)
    timeline.spines[["right", "top"]].set_visible(False)
    timeline.spines["left"].set_visible(True)
    timeline.spines["left"].set_color(COLORS["muted"])
    timeline.spines["bottom"].set_color(COLORS["muted"])
    timeline.tick_params(axis="x", length=3, color=COLORS["muted"])
    timeline.tick_params(
        axis="x", which="minor", length=2, width=0.6, color=COLORS["muted"]
    )
    timeline.tick_params(
        axis="y",
        length=3,
        width=0.7,
        color=COLORS["muted"],
        pad=5,
        labelsize=8.2,
    )
    for label in timeline.get_yticklabels():
        label.set_horizontalalignment("right")
        label.set_fontweight("bold")
    timeline_block(
        timeline,
        2019,
        2021,
        2.72,
        0.56,
        COLORS["calibration"],
        "Calibration\n69 c | 4 e",
        fontsize=8.1,
    )
    timeline_block(
        timeline,
        2021,
        2022,
        2.70,
        0.60,
        COLORS["historical"],
        "Hist. eval.\n69 c | 4 e",
        fontsize=8.0,
    )
    timeline.annotate(
        "",
        xy=(2021.06, 3.00),
        xytext=(2020.94, 3.00),
        arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": COLORS["muted"]},
    )

    timeline_block(
        timeline,
        2022,
        2025,
        2.00,
        0.31,
        COLORS["calibration"],
        "Original derivation\n44 c | 31 e",
        fontsize=8.0,
    )
    timeline_block(
        timeline,
        2022,
        2025,
        1.62,
        0.31,
        COLORS["evaluation"],
        "Expansion evaluation\n31 c | 31 e",
        fontsize=8.0,
    )
    timeline_block(
        timeline,
        2025,
        2026,
        1.62,
        0.69,
        COLORS["evaluation"],
        "OOS\nevaluation\n75 c | 10 e",
        fontsize=8.0,
    )
    timeline.annotate(
        "",
        xy=(2025.06, 1.96),
        xytext=(2024.94, 1.96),
        arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": COLORS["muted"]},
    )

    timeline_block(
        timeline,
        2025,
        2026,
        0.56,
        0.50,
        COLORS["calibration"],
        "Calibration\n75 c | 10 e",
        fontsize=8.0,
    )
    timeline_block(
        timeline,
        2026,
        2027,
        0.56,
        0.50,
        COLORS["prospective"],
        "Holdout\n75 c | 8 e",
        fontsize=8.0,
    )
    timeline.annotate(
        "",
        xy=(2026.06, 0.81),
        xytext=(2025.94, 0.81),
        arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": COLORS["muted"]},
    )

    legend = [
        Patch(facecolor=COLORS["calibration"], edgecolor="none", label="Calibration / derivation"),
        Patch(facecolor=COLORS["evaluation"], edgecolor="none", label="Out-of-sample evaluation"),
        Patch(facecolor=COLORS["historical"], edgecolor="none", label="Historical external evaluation"),
        Patch(facecolor=COLORS["prospective"], edgecolor="none", label="Prospective holdout"),
    ]
    fig.legend(
        handles=legend,
        loc="upper left",
        bbox_to_anchor=(0.200, 0.565),
        bbox_transform=fig.transFigure,
        frameon=False,
        ncol=2,
        handlelength=1.3,
        columnspacing=1.2,
        borderaxespad=0,
        fontsize=8.0,
    )
    timeline.annotate(
        "",
        xy=(2025.50, 1.07),
        xytext=(2025.50, 1.61),
        arrowprops={"arrowstyle": "-|>", "lw": 0.7, "color": COLORS["muted"]},
    )
    timeline.text(
        2025.39,
        1.34,
        "also calibration\nsource",
        ha="right",
        va="center",
        fontsize=8.0,
        color=COLORS["muted"],
    )
    return fig

def clean_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(direction="out", length=3, width=0.7)

def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.24,
        1.12,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12,
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
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(6.879, 7.40),
        constrained_layout=True,
        gridspec_kw={"width_ratios": [0.88, 1.22]},
    )
    fig.set_constrained_layout_pads(
        w_pad=0.06,
        h_pad=0.07,
        wspace=0.30,
        hspace=0.30,
    )
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
            fontsize=8.2,
        )
    ax_a.axvline(0, color=COLORS["ink"], linewidth=0.8)
    ax_a.set_yticks(y, labels)
    ax_a.set_ylim(1.90, -0.25)
    ax_a.set_xlim(min(-5.,float(low_pct.min())-5),max(5.,float(high_pct.max())+8))
    ax_a.set_xlabel("Observed RMSE\nreduction (%)")
    panel_label(ax_a, "a")
    clean_axis(ax_a)

    events = data["single_events"].copy()
    events["start_date"] = pd.to_datetime(events["start_date"])
    base_y = np.arange(len(events))
    offsets = {"core": -0.20, "ring": 0.0, "anomaly": 0.20}
    for component, color, label in zip(components, colors, labels):
        values = events[f"{component}_rmse_reduction_fraction"].to_numpy() * 100
        # The smallest observed contrast reduction is only 0.857%. Give that
        # point a compact marker so its complete glyph remains on the positive
        # side of the exact zero reference line.
        marker_sizes = np.where(values < 1.2, 6.0, 27.0)
        ax_b.scatter(
            values,
            base_y + offsets[component],
            s=marker_sizes,
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
    vv=100*events[['core_rmse_reduction_fraction','ring_rmse_reduction_fraction','anomaly_rmse_reduction_fraction']].to_numpy();ax_b.set_xlim(min(-2.,float(vv.min())-3),max(5.,float(vv.max())+5))
    ax_b.margins(x=0)
    ax_b.set_xlabel("Interval-specific RMSE\nreduction (%)")
    component_handles = component_legend_handles()
    ax_b.legend(
        handles=component_handles,
        loc="lower left",
        bbox_to_anchor=(-0.023, 1.01),
        frameon=False,
        ncol=1,
        borderaxespad=0,
        handletextpad=0.3,
        labelspacing=0.25,
        fontsize=8.0,
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
    term_colors = [
        COLORS["variance"],
        COLORS["bias"],
        COLORS["covariance"],
        COLORS["prospective"],
    ]
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
        ax_c.errorbar(
            point,
            yi,
            xerr=np.array([[point - low], [high - point]]),
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=1.6,
            capsize=3.5,
            markersize=5.0,
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
            fontsize=8.2,
        )
    ax_c.axvline(0, color=COLORS["ink"], linewidth=0.8)
    ax_c.set_yticks(term_y, term_labels)
    ax_c.set_ylim(2.28, -0.25)
    span=max(.1,float(highs.max()-lows.min()));ax_c.set_xlim(float(lows.min())-.12*span,float(highs.max())+.12*span)
    ax_c.set_xlabel("Observed contribution to\nMSE gain (K²)")
    panel_label(ax_c, "c")
    clean_axis(ax_c)

    gate = data["gate_cohorts"].set_index("scope_label").loc[
        ["combined", "original", "expansion"]
    ]
    cohort_labels = [f"{label}\n{role}\nn={int(gate.loc[key,'n_transitions'])}" for label,role,key in [('Combined','evaluation','combined'),('Original','diagnostic','original'),('Expansion','diagnostic','expansion')]]
    gate_metrics = ["coverage", "certified_fraction", "certified_sign_accuracy"]
    gate_labels = ["Coverage", "Sign supported", "G18 sign agreement"]
    gate_colors = [COLORS["core"], COLORS["ring"], COLORS["contrast"]]
    # Separate group centers and narrow the bars slightly so the three cohort
    # labels and the bar annotations have distinct visual lanes.
    x = np.array([0.0, 1.25, 2.50])
    bar_offset = 0.30
    bar_width = 0.17
    percentage_label_lifts = [1.0, 1.2, 6.0]
    for index, (metric, label, color) in enumerate(zip(gate_metrics, gate_labels, gate_colors)):
        values = gate[metric].to_numpy() * 100
        positions = x + (index - 1) * bar_offset
        bars = ax_d.bar(
            positions,
            values,
            width=bar_width,
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
                value + percentage_label_lifts[index],
                f"{value:.1f}",
                ha="center",
                va="bottom",
                fontsize=6.6,
            )
            ax_d.text(
                bar.get_x() + bar.get_width() / 2,
                max(2.0, min(value * 0.48, value - 5.0)),
                fraction,
                ha="center",
                va="center",
                rotation=90,
                fontsize=6.2,
                color=COLORS["ink"],
                fontweight="bold",
            )
    ax_d.set_xticks(x, cohort_labels)
    ax_d.set_xlim(-0.45, 2.95)
    ax_d.set_ylim(0, 120)
    ax_d.set_yticks(np.arange(0, 121, 20))
    ax_d.margins(y=0)
    ax_d.set_ylabel("Held-out transitions (%)")
    gate_handles, gate_legend_labels = ax_d.get_legend_handles_labels()
    ax_d.legend(
        handles=gate_handles,
        labels=gate_legend_labels,
        loc="lower left",
        bbox_to_anchor=(0.023, 1.01),
        frameon=False,
        ncol=1,
        labelspacing=0.25,
        handlelength=1.1,
        fontsize=8.0,
        borderaxespad=0,
    )
    ax_d.tick_params(axis="x", labelsize=7.2, pad=5)
    for label in ax_d.get_xticklabels():
        label.set_linespacing(1.15)
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
                "Date": "2026-10-29",
            }
        else:
            metadata = {"Software": "build_submission_figures.py"}
        fig.savefig(
            path,
            dpi=600 if extension == "png" else None,
            # Keep the exact final-placement canvas dimensions. All content is
            # explicitly laid out inside the canvas and checked for clipping.
            bbox_inches=None,
            facecolor="white",
            metadata=metadata,
        )
        if extension == "png":
            # Matplotlib writes an alpha channel even on a white canvas. The
            # journal requests ordinary 8-bit RGB artwork, so flatten the
            # already-white export without changing any plotted content.
            with Image.open(path) as exported_png:
                exported_png.convert("RGB").save(path, dpi=(600, 600))
        if extension == "svg":
            svg_text = path.read_text(encoding="utf-8")
            path.write_text(
                "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
                encoding="utf-8",
            )
    plt.close(fig)
