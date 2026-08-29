from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "02_EVIDENCE"
OUT = ROOT / "03_FIGURES"
RMSE_SOURCE = EVIDENCE / "tables/downstream_metric_framework_figure_rmse_source.csv"
BUDGET_SOURCE = EVIDENCE / "tables/downstream_metric_framework_figure_budget_source.csv"
UNCERTAINTY_SOURCE = EVIDENCE / "si_tables/uncertainty_gate_2026_by_cohort_event.csv"
FIXED_EXPORT_TIME = datetime(2026, 8, 12, tzinfo=timezone.utc)

SAMPLE_ORDER = [
    "2021 external GOES17/16",
    "2022-2024 expansion GOES18/16",
    "2025 original GOES18/19",
    "2025 expansion GOES18/19",
    "2026 combined GOES18/19",
]

COLORS = {
    "core": "#0072B2",
    "ring": "#009E73",
    "anomaly": "#CC79A7",
    "variance": "#56B4E9",
    "bias": "#E69F00",
    "covariance": "#D55E00",
    "net": "#222222",
    "certified": "#0072B2",
    "abstain": "#B8B8B8",
}


def panel_label(axis: plt.Axes, label: str, y: float = 1.035) -> None:
    axis.text(
        -0.11,
        y,
        label,
        transform=axis.transAxes,
        fontsize=11,
        fontweight="bold",
        va="top",
        ha="left",
    )


def add_box(
    axis: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    facecolor: str,
    edgecolor: str,
    fontsize: float = 7.5,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.015",
        linewidth=0.8,
        facecolor=facecolor,
        edgecolor=edgecolor,
        transform=axis.transAxes,
    )
    axis.add_patch(patch)
    axis.text(
        x + width / 2,
        y + height / 2,
        text,
        transform=axis.transAxes,
        ha="center",
        va="center",
        fontsize=fontsize,
    )


def add_arrow(
    axis: plt.Axes, start: tuple[float, float], end: tuple[float, float]
) -> None:
    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            transform=axis.transAxes,
            arrowstyle="-|>",
            mutation_scale=9,
            linewidth=0.8,
            color="#555555",
        )
    )


def load_rmse() -> pd.DataFrame:
    frame = pd.read_csv(RMSE_SOURCE)
    expected_pairs = {
        (sample, component)
        for sample in SAMPLE_ORDER
        for component in ["core", "ring", "anomaly"]
    }
    observed_pairs = set(zip(frame["sample"], frame["component"]))
    if observed_pairs != expected_pairs or len(frame) != len(expected_pairs):
        raise ValueError("Figure 2 RMSE source does not contain the expected 15 rows")
    frame["sample"] = pd.Categorical(frame["sample"], SAMPLE_ORDER, ordered=True)
    return frame.sort_values(["sample", "component"])


def load_budgets() -> pd.DataFrame:
    frame = pd.read_csv(BUDGET_SOURCE)
    if (
        len(frame) != len(SAMPLE_ORDER)
        or set(frame["sample"]) != set(SAMPLE_ORDER)
        or not frame["scope"].eq("hourly").all()
    ):
        raise ValueError("Figure 2 budget source does not contain five hourly cohorts")
    if frame["budget_closure_residual_k2"].abs().max() > 1e-10:
        raise ValueError("Figure 2 budget source fails the 1e-10 K^2 closure check")
    frame["sample"] = pd.Categorical(frame["sample"], SAMPLE_ORDER, ordered=True)
    return frame.sort_values("sample")


def load_uncertainty() -> pd.DataFrame:
    frame = pd.read_csv(UNCERTAINTY_SOURCE)
    frame = frame[frame["scope_type"].eq("cohort")].copy()
    frame = frame.rename(columns={"scope_label": "cohort", "n_transitions": "n"})
    combined = frame[frame["cohort"].eq("combined")]
    if len(combined) != 1:
        raise ValueError("Figure 2 uncertainty source lacks one combined cohort row")
    observed = combined.iloc[0]
    counts = (
        int(observed["n"]),
        int(observed["n_certified"]),
        int(observed["n_certified_correct"]),
    )
    if counts != (588, 180, 174):
        raise ValueError(f"Unexpected combined residual-interval counts: {counts}")
    return frame


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.linewidth": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.hashsalt": "gsis-downstream-framework-v1",
        }
    )
    # The extra canvas width provides dedicated space for the legends in
    # panels b and c without changing their scientific x-axis ranges.
    figure, axes = plt.subplots(2, 2, figsize=(11.6, 7.0))
    figure.subplots_adjust(
        left=0.075,
        right=0.825,
        bottom=0.11,
        top=0.95,
        wspace=0.52,
        hspace=0.40,
    )
    ax_a, ax_b, ax_c, ax_d = axes.ravel()

    ax_a.set_axis_off()
    add_box(ax_a, 0.02, 0.71, 0.21, 0.14, "Core LST\nC", "#EAF4FB", COLORS["core"])
    add_box(ax_a, 0.02, 0.48, 0.21, 0.14, "Ring LST\nR", "#EAF8F3", COLORS["ring"])
    add_box(
        ax_a,
        0.32,
        0.60,
        0.25,
        0.16,
        r"Spatial contrast" "\n" r"$D = C - R$",
        "#FAEFF7",
        COLORS["anomaly"],
    )
    add_box(
        ax_a,
        0.66,
        0.60,
        0.32,
        0.16,
        r"Temporal transition" "\n" r"$T = D_{\mathrm{post}} - D_{\mathrm{pre}}$",
        "#F4F4F4",
        "#666666",
    )
    add_arrow(ax_a, (0.24, 0.78), (0.31, 0.70))
    add_arrow(ax_a, (0.24, 0.55), (0.31, 0.66))
    add_arrow(ax_a, (0.58, 0.68), (0.65, 0.68))
    add_box(
        ax_a,
        0.02,
        0.31,
        0.55,
        0.10,
        "Out-of-sample loss at each measurand",
        "#F7F7F7",
        "#777777",
        7,
    )
    add_box(
        ax_a,
        0.02,
        0.07,
        0.22,
        0.14,
        "Loss improves\napply selected\ncorrection",
        "#EEF8F4",
        "#6A9E86",
        6.5,
    )
    add_box(
        ax_a,
        0.265,
        0.07,
        0.22,
        0.14,
        "No justified gain\nretain raw\nmeasurand",
        "#F4F4F4",
        "#888888",
        6.5,
    )
    add_arrow(ax_a, (0.13, 0.30), (0.13, 0.22))
    add_arrow(ax_a, (0.375, 0.30), (0.375, 0.22))
    add_box(
        ax_a,
        0.60,
        0.31,
        0.38,
        0.10,
        "Empirical residual interval\nfor transition sign",
        "#F7F3FA",
        "#7A5AA6",
        6.8,
    )
    add_box(
        ax_a,
        0.51,
        0.07,
        0.195,
        0.14,
        "Interval excludes\nzero\nsign supported",
        "#EEF8F4",
        "#6A9E86",
        5.7,
    )
    add_box(
        ax_a,
        0.73,
        0.07,
        0.25,
        0.14,
        "Interval includes\nzero\nabstain",
        "#FFF3EB",
        "#C86428",
        5.7,
    )
    add_arrow(ax_a, (0.6075, 0.30), (0.6075, 0.22))
    add_arrow(ax_a, (0.855, 0.30), (0.855, 0.22))
    panel_label(ax_a, "a")

    rmse = load_rmse()
    samples = list(rmse["sample"].cat.categories)
    sample_labels = [
        "2021 G17/16 external",
        "2022–24 G18/16 expansion",
        "2025 G18/19 original",
        "2025 G18/19 expansion",
        "2026 G18/19 prospective",
    ]
    y = np.arange(len(samples))
    offsets = {"core": -0.17, "ring": 0.0, "anomaly": 0.17}
    labels = {"core": "Core", "ring": "Ring", "anomaly": "Core−ring contrast"}
    for component in ["core", "ring", "anomaly"]:
        selected = rmse[rmse["component"].eq(component)].set_index("sample")
        values = np.array(
            [selected.loc[sample, "rmse_reduction_fraction"] for sample in samples]
        )
        ax_b.scatter(
            values * 100,
            y + offsets[component],
            s=34,
            color=COLORS[component],
            edgecolor="white",
            linewidth=0.4,
            label=labels[component],
            zorder=3,
        )
    ax_b.axvline(0, color="#666666", linewidth=0.7)
    ax_b.set_yticks(y, sample_labels)
    ax_b.invert_yaxis()
    ax_b.set_xlabel("Out-of-sample RMSE reduction (%)")
    ax_b.legend(
        frameon=False,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        borderaxespad=0,
    )
    ax_b.set_xlim(-18, 72)
    panel_label(ax_b, "b")

    budgets = load_budgets()
    x = np.arange(len(budgets))
    width = 0.22
    variance = budgets["component_variance_gain_k2"].to_numpy()
    bias = budgets["differential_bias_gain_k2"].to_numpy()
    penalty = -budgets["covariance_loss_penalty_k2"].to_numpy()
    net = budgets["net_downstream_mse_gain_k2"].to_numpy()
    ax_c.bar(
        x - width,
        variance,
        width,
        color=COLORS["variance"],
        label="Component variance gain",
    )
    ax_c.bar(x, bias, width, color=COLORS["bias"], label="Differential-bias gain")
    ax_c.bar(
        x + width,
        penalty,
        width,
        color=COLORS["covariance"],
        label="Covariance-loss penalty",
    )
    ax_c.scatter(
        x,
        net,
        s=20,
        marker="o",
        color=COLORS["net"],
        edgecolor="none",
        label="Net downstream gain",
        zorder=4,
    )
    ax_c.axhline(0, color="#555555", linewidth=0.7)
    ax_c.set_xticks(x, ["2021\nG17/16", "2022–24\nG18/16", "2025 orig.\nG18/19", "2025 expand.\nG18/19", "2026\nG18/19"])
    ax_c.set_ylabel("Exact hourly MSE decomposition term (K²)")
    ax_c.set_ylim(min(-2.7, float(penalty.min()) - 0.15), 3.0)
    ax_c.legend(
        frameon=False,
        loc="upper right",
        bbox_to_anchor=(0.99, 0.985),
        borderaxespad=0,
        ncol=2,
        fontsize=6.2,
        handlelength=1.5,
        columnspacing=0.8,
    )
    panel_label(ax_c, "c", y=1.10)

    uncertainty = load_uncertainty()
    combined = uncertainty[uncertainty["cohort"].eq("combined")].iloc[0]
    total = int(combined["n"])
    certified = int(combined["n_certified"])
    agrees = int(round(certified * combined["certified_sign_accuracy"]))
    differs = certified - agrees
    abstain = total - certified
    values = [agrees, differs, abstain]
    labels = ["Agrees with G18", "Differs from G18", "Abstained"]
    colors = [COLORS["certified"], COLORS["covariance"], COLORS["abstain"]]
    left = 0
    bar_y = 0.18
    bar_height = 0.18
    for value, label, color in zip(values, labels, colors):
        ax_d.barh(
            bar_y,
            value,
            left=left,
            height=bar_height,
            color=color,
            label=label,
        )
        if value >= 20:
            ax_d.text(
                left + value / 2,
                bar_y,
                str(value),
                ha="center",
                va="center",
                color="white" if color != COLORS["abstain"] else "#222222",
                fontsize=8,
                fontweight="bold",
            )
        else:
            ax_d.annotate(
                str(value),
                xy=(left + value / 2, bar_y + bar_height / 2),
                xytext=(left + value / 2, bar_y + 0.23),
                ha="center",
                va="bottom",
                fontsize=7,
                fontweight="bold",
                arrowprops={"arrowstyle": "-", "lw": 0.6, "color": "#555555"},
            )
        left += value
    ax_d.set_xlim(0, total)
    ax_d.set_ylim(0, 0.92)
    ax_d.set_yticks([])
    ax_d.set_xlabel("Held-out 2026 city-event transitions")
    ax_d.spines["left"].set_visible(False)
    ax_d.tick_params(axis="y", left=False)
    ax_d.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.93),
        ncol=3,
        borderaxespad=0,
    )
    ax_d.text(
        0.5,
        0.57,
        f"{combined['coverage']*100:.1f}% interval coverage; interval excluded zero for "
        f"{certified}/{total} ({combined['certified_fraction']*100:.1f}%)\n"
        f"Supported signs agreed with GOES-18 for {agrees}/{certified} "
        f"({combined['certified_sign_accuracy']*100:.1f}%)",
        transform=ax_d.transAxes,
        ha="center",
        va="center",
        fontsize=8,
    )
    panel_label(ax_d, "d")

    for axis in [ax_b, ax_c, ax_d]:
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(length=3, width=0.7)

    OUT.mkdir(parents=True, exist_ok=True)
    for suffix in ["png", "pdf", "svg"]:
        metadata = None
        if suffix == "pdf":
            metadata = {
                "Creator": "build_downstream_metric_framework_figure.py",
                "CreationDate": FIXED_EXPORT_TIME,
                "ModDate": FIXED_EXPORT_TIME,
            }
        elif suffix == "svg":
            metadata = {"Date": "2026-08-12"}
        figure.savefig(
            OUT / f"downstream_metric_framework_synthesis.{suffix}",
            dpi=400 if suffix == "png" else None,
            bbox_inches="tight",
            metadata=metadata,
        )
        if suffix == "svg":
            svg_path = OUT / "downstream_metric_framework_synthesis.svg"
            svg_text = svg_path.read_text(encoding="utf-8")
            svg_path.write_text(
                "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
                encoding="utf-8",
            )
    plt.close(figure)

    caption = (
        "**Figure 2. Cross-cohort component gains, downstream non-transfer, and selective "
        "directional inference.** **(a)** Measurement hierarchy, loss-based correction or "
        "raw-retention rule, and separate residual-interval rule for sign support or "
        "abstention. Core is urban-core land surface temperature (LST), ring is the fixed "
        "10–20-km surrounding-ring LST, and \\(T=D_{\\mathrm{post}}-D_{\\mathrm{pre}}\\). "
        "**(b)** Out-of-sample root-mean-squared error "
        "(RMSE) reductions across three reference/source platform pairings and five evaluation "
        "cohorts; the vertical zero line marks no RMSE change. **(c)** Exact hourly "
        "mean-squared-error (MSE) decomposition. Positive "
        "component-variance and differential-bias gains are offset by loss of beneficial "
        "core–ring residual covariance; filled circles show net downstream MSE gain, and the "
        "horizontal zero line marks no gain. **(d)** The "
        "prespecified 2026 residual interval covered 90.0% of 588 GOES-18 reference-platform "
        "transitions and excluded zero for 180 cases (30.6%); the supported sign agreed with "
        "GOES-18 in 174 cases (96.7%). Segment counts show the corresponding cases in the "
        "stacked bar."
    )
    (OUT / "downstream_metric_framework_synthesis_caption.md").write_text(
        caption, encoding="utf-8"
    )
    print(OUT / "downstream_metric_framework_synthesis.png")


if __name__ == "__main__":
    main()
