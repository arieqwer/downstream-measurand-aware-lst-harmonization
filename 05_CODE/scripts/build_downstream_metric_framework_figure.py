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


def panel_label(axis: plt.Axes, label: str) -> None:
    axis.text(
        -0.12,
        1.04,
        label,
        transform=axis.transAxes,
        fontsize=11,
        fontweight="bold",
        va="top",
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
        raise ValueError("Figure 3 RMSE source does not contain the expected 15 rows")
    frame["sample"] = pd.Categorical(frame["sample"], SAMPLE_ORDER, ordered=True)
    return frame.sort_values(["sample", "component"])


def load_budgets() -> pd.DataFrame:
    frame = pd.read_csv(BUDGET_SOURCE)
    if (
        len(frame) != len(SAMPLE_ORDER)
        or set(frame["sample"]) != set(SAMPLE_ORDER)
        or not frame["scope"].eq("hourly").all()
    ):
        raise ValueError("Figure 3 budget source does not contain five hourly cohorts")
    if frame["budget_closure_residual_k2"].abs().max() > 1e-10:
        raise ValueError("Figure 3 budget source fails the 1e-10 K^2 closure gate")
    frame["sample"] = pd.Categorical(frame["sample"], SAMPLE_ORDER, ordered=True)
    return frame.sort_values("sample")


def load_uncertainty() -> pd.DataFrame:
    frame = pd.read_csv(UNCERTAINTY_SOURCE)
    frame = frame[frame["scope_type"].eq("cohort")].copy()
    frame = frame.rename(columns={"scope_label": "cohort", "n_transitions": "n"})
    combined = frame[frame["cohort"].eq("combined")]
    if len(combined) != 1:
        raise ValueError("Figure 3 uncertainty source lacks one combined cohort row")
    observed = combined.iloc[0]
    counts = (
        int(observed["n"]),
        int(observed["n_certified"]),
        int(observed["n_certified_correct"]),
    )
    if counts != (588, 180, 174):
        raise ValueError(f"Unexpected combined uncertainty-gate counts: {counts}")
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
    figure, axes = plt.subplots(2, 2, figsize=(10.2, 7.2))
    figure.subplots_adjust(
        left=0.09, right=0.985, bottom=0.11, top=0.95, wspace=0.46, hspace=0.36
    )
    ax_a, ax_b, ax_c, ax_d = axes.ravel()

    ax_a.set_axis_off()
    ax_a.set_title("Loss selection and sign uncertainty determine distinct actions", loc="left")
    add_box(ax_a, 0.04, 0.71, 0.23, 0.14, "Core LST\nC", "#EAF4FB", COLORS["core"])
    add_box(ax_a, 0.04, 0.48, 0.23, 0.14, "Ring LST\nR", "#EAF8F3", COLORS["ring"])
    add_box(
        ax_a,
        0.39,
        0.60,
        0.25,
        0.16,
        "Spatial contrast\nD = C - R",
        "#FAEFF7",
        COLORS["anomaly"],
    )
    add_box(
        ax_a,
        0.73,
        0.60,
        0.24,
        0.16,
        "Temporal transition\nT = Dpost - Dpre",
        "#F4F4F4",
        "#666666",
    )
    add_arrow(ax_a, (0.28, 0.78), (0.38, 0.70))
    add_arrow(ax_a, (0.28, 0.55), (0.38, 0.66))
    add_arrow(ax_a, (0.65, 0.68), (0.72, 0.68))
    add_box(
        ax_a,
        0.04,
        0.31,
        0.58,
        0.10,
        "Out-of-sample loss at each measurand",
        "#F7F7F7",
        "#777777",
        7,
    )
    add_box(
        ax_a,
        0.04,
        0.07,
        0.27,
        0.14,
        "Loss improves\nApply selected\ncorrection",
        "#EEF8F4",
        "#6A9E86",
        6.5,
    )
    add_box(
        ax_a,
        0.35,
        0.07,
        0.27,
        0.14,
        "No justified gain\nRetain raw\nmeasurand",
        "#F4F4F4",
        "#888888",
        6.5,
    )
    add_arrow(ax_a, (0.20, 0.30), (0.175, 0.22))
    add_arrow(ax_a, (0.46, 0.30), (0.485, 0.22))
    add_box(
        ax_a,
        0.68,
        0.31,
        0.29,
        0.10,
        "Empirical residual interval\nfor transition sign",
        "#F7F3FA",
        "#7A5AA6",
        6.8,
    )
    add_box(
        ax_a,
        0.68,
        0.07,
        0.13,
        0.14,
        "Excludes 0\nResolve sign",
        "#EEF8F4",
        "#6A9E86",
        6.6,
    )
    add_box(
        ax_a,
        0.84,
        0.07,
        0.13,
        0.14,
        "Includes 0\nAbstain",
        "#FFF3EB",
        "#C86428",
        6.6,
    )
    add_arrow(ax_a, (0.77, 0.30), (0.745, 0.22))
    add_arrow(ax_a, (0.88, 0.30), (0.905, 0.22))
    panel_label(ax_a, "a")

    rmse = load_rmse()
    samples = list(rmse["sample"].cat.categories)
    sample_labels = [
        "2021 G17/16 external",
        "2022-24 G18/16 expansion",
        "2025 G18/19 original",
        "2025 G18/19 expansion",
        "2026 G18/19 prospective",
    ]
    y = np.arange(len(samples))
    offsets = {"core": -0.17, "ring": 0.0, "anomaly": 0.17}
    labels = {"core": "Core", "ring": "Ring", "anomaly": "Core-minus-ring"}
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
    ax_b.set_title("Component gains transfer inconsistently to the difference", loc="left")
    ax_b.legend(frameon=False, loc="lower right")
    ax_b.grid(axis="x", color="#E6E6E6", linewidth=0.6)
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
        s=32,
        marker="D",
        color=COLORS["net"],
        edgecolor="white",
        linewidth=0.4,
        label="Net downstream gain",
        zorder=4,
    )
    ax_c.axhline(0, color="#555555", linewidth=0.7)
    ax_c.set_xticks(x, ["2021\nG17/16", "2022-24\nG18/16", "2025 orig.\nG18/19", "2025 expand.\nG18/19", "2026\nG18/19"])
    ax_c.set_ylabel("Exact hourly MSE-budget term (K²)")
    ax_c.set_title("Covariance loss offsets upstream variance reduction", loc="left")
    ax_c.legend(frameon=False, ncol=2, loc="lower left")
    ax_c.grid(axis="y", color="#E6E6E6", linewidth=0.6)
    panel_label(ax_c, "c")

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
    for value, label, color in zip(values, labels, colors):
        ax_d.barh(0, value, left=left, height=0.45, color=color, label=label)
        if value >= 20:
            ax_d.text(
                left + value / 2,
                0,
                str(value),
                ha="center",
                va="center",
                color="white" if color != COLORS["abstain"] else "#222222",
                fontsize=8,
                fontweight="bold",
            )
        else:
            ax_d.text(
                left + value / 2,
                0.31,
                str(value),
                ha="center",
                va="bottom",
                color="#222222",
                fontsize=7,
                fontweight="bold",
            )
        left += value
    ax_d.set_xlim(0, total)
    ax_d.set_ylim(-0.65, 0.65)
    ax_d.set_yticks([])
    ax_d.set_xlabel("Held-out 2026 city-event transitions")
    ax_d.set_title("Residual interval permits selective inference", loc="left")
    ax_d.legend(frameon=False, loc="upper center", ncol=3)
    ax_d.text(
        0.02,
        0.12,
        f"{combined['coverage']*100:.1f}% interval\ncoverage",
        transform=ax_d.transAxes,
        ha="left",
        va="bottom",
        fontsize=8,
    )
    ax_d.text(
        0.98,
        0.12,
        f"{combined['certified_fraction']*100:.1f}% resolved\n"
        f"{combined['certified_sign_accuracy']*100:.1f}% agreement\n"
        "with GOES-18 sign",
        transform=ax_d.transAxes,
        ha="right",
        va="bottom",
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
    plt.close(figure)

    caption = (
        "**Figure 3. Cross-cohort component gains, downstream non-transfer, and "
        "selective inference.** **a,** Measurement hierarchy and distinct "
        "measurand-level actions. Out-of-sample loss selects correction or raw "
        "retention for each measurand; the empirical residual interval separately "
        "resolves the transition sign or abstains. **b,** Out-of-sample RMSE "
        "reductions across three platform pairings and five evaluation cohorts. "
        "Core and ring agreement improved in "
        "every evaluation cohort, whereas core-minus-ring performance was "
        "inconsistent. **c,** "
        "Exact hourly MSE decomposition. Positive component variance and "
        "differential-bias gains are offset by loss of beneficial core-ring error "
        "covariance; diamonds show the resulting net downstream gain. **d,** The "
        "prespecified 2026 residual interval attained 90.0% coverage and resolved 30.6% of "
        "588 transition directions, with 96.7% agreement with the GOES-18 sign "
        "among resolved directions."
    )
    (OUT / "downstream_metric_framework_synthesis_caption.md").write_text(
        caption, encoding="utf-8"
    )
    print(OUT / "downstream_metric_framework_synthesis.png")


if __name__ == "__main__":
    main()
