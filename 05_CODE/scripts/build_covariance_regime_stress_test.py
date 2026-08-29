from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "02_EVIDENCE"
SIMULATION = EVIDENCE / "simulation"
FIGURES = ROOT / "03_FIGURES"
POINT_BUDGETS = EVIDENCE / "tables" / "exact_mse_budgets_with_external.csv"

RHO_RAW = np.linspace(0.0, 0.95, 96)
RHO_HARM = np.linspace(0.0, 0.95, 96)
RAW_CORE_TO_RING_SD_RATIO = np.array([0.85, 0.95, 1.05, 1.15, 1.25])
CORE_SD_RATIO = np.array([0.45, 0.55, 0.65, 0.75, 0.85, 0.95])
RING_SD_RATIO = np.array([0.45, 0.55, 0.65, 0.75, 0.85, 0.95])
DIFFERENTIAL_BIAS_GAIN = np.array([-0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15])
TOLERANCE = 1e-12


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def downstream_gain(
    rho_raw: np.ndarray,
    rho_harm: np.ndarray,
    raw_core_sd: np.ndarray,
    raw_ring_sd: np.ndarray,
    core_sd_ratio: np.ndarray,
    ring_sd_ratio: np.ndarray,
    differential_bias_gain: np.ndarray,
) -> np.ndarray:
    """Return standardized raw-to-harmonized MSE gain for C - R.

    Raw component error variances are normalized to average one. The two SD
    ratios specify harmonized/raw component error SD. The differential-bias
    term is (delta_b_raw^2 - delta_b_harm^2) on the same variance scale.
    """

    variance_gain = (
        raw_core_sd**2 * (1.0 - core_sd_ratio**2)
        + raw_ring_sd**2 * (1.0 - ring_sd_ratio**2)
    )
    covariance_penalty = 2.0 * (
        rho_raw * raw_core_sd * raw_ring_sd
        - rho_harm
        * raw_core_sd
        * raw_ring_sd
        * core_sd_ratio
        * ring_sd_ratio
    )
    return variance_gain + differential_bias_gain - covariance_penalty


def enumerate_regimes() -> tuple[pd.DataFrame, dict[str, object]]:
    raw_ring_sd = np.sqrt(2.0 / (RAW_CORE_TO_RING_SD_RATIO**2 + 1.0))
    raw_core_sd = RAW_CORE_TO_RING_SD_RATIO * raw_ring_sd
    gain = downstream_gain(
        RHO_RAW[:, None, None, None, None, None],
        RHO_HARM[None, :, None, None, None, None],
        raw_core_sd[None, None, :, None, None, None],
        raw_ring_sd[None, None, :, None, None, None],
        CORE_SD_RATIO[None, None, None, :, None, None],
        RING_SD_RATIO[None, None, None, None, :, None],
        DIFFERENTIAL_BIAS_GAIN[None, None, None, None, None, :],
    )
    nuisance_axes = (2, 3, 4, 5)
    positive = gain > TOLERANCE
    negative = gain < -TOLERANCE
    boundary = ~(positive | negative)
    quantiles = np.quantile(gain, [0.05, 0.5, 0.95], axis=nuisance_axes)
    minimum = gain.min(axis=nuisance_axes)
    maximum = gain.max(axis=nuisance_axes)

    raw_grid, harm_grid = np.meshgrid(RHO_RAW, RHO_HARM, indexing="ij")
    frame = pd.DataFrame(
        {
            "rho_raw": raw_grid.ravel(),
            "rho_harmonized": harm_grid.ravel(),
            "n_bounded_configurations": int(
                len(CORE_SD_RATIO)
                * len(RAW_CORE_TO_RING_SD_RATIO)
                * len(RING_SD_RATIO)
                * len(DIFFERENTIAL_BIAS_GAIN)
            ),
            "fraction_downstream_gain": positive.mean(axis=nuisance_axes).ravel(),
            "fraction_downstream_damage": negative.mean(axis=nuisance_axes).ravel(),
            "fraction_boundary": boundary.mean(axis=nuisance_axes).ravel(),
            "minimum_standardized_gain": minimum.ravel(),
            "p05_standardized_gain": quantiles[0].ravel(),
            "median_standardized_gain": quantiles[1].ravel(),
            "p95_standardized_gain": quantiles[2].ravel(),
            "maximum_standardized_gain": maximum.ravel(),
        }
    )
    frame["bounded_regime"] = np.select(
        [
            frame["minimum_standardized_gain"] > TOLERANCE,
            frame["maximum_standardized_gain"] < -TOLERANCE,
        ],
        ["necessarily_helps", "necessarily_damages"],
        default="parameter_dependent",
    )
    summary = {
        "method": "deterministic exact enumeration; no random sampling",
        "identity": (
            "G_D = sigma_c_raw^2 * (1 - q_c^2) + sigma_r_raw^2 * "
            "(1 - q_r^2) + G_bias - 2 * sigma_c_raw * sigma_r_raw * "
            "(rho_raw - rho_harmonized * q_c * q_r)"
        ),
        "normalization": (
            "mean raw core/ring residual variance equals 1; the raw core:ring "
            "SD ratio varies; q_c and q_r are harmonized/raw residual-SD "
            "ratios; G_bias is the raw-minus-harmonized differential-bias-"
            "squared gain standardized by mean raw component variance"
        ),
        "bounds": {
            "rho_raw": RHO_RAW.tolist(),
            "rho_harmonized": RHO_HARM.tolist(),
            "raw_core_to_ring_sd_ratio": RAW_CORE_TO_RING_SD_RATIO.tolist(),
            "core_sd_ratio": CORE_SD_RATIO.tolist(),
            "ring_sd_ratio": RING_SD_RATIO.tolist(),
            "standardized_differential_bias_gain": DIFFERENTIAL_BIAS_GAIN.tolist(),
        },
        "n_correlation_cells": int(len(frame)),
        "n_nuisance_configurations_per_cell": int(
            len(CORE_SD_RATIO)
            * len(RAW_CORE_TO_RING_SD_RATIO)
            * len(RING_SD_RATIO)
            * len(DIFFERENTIAL_BIAS_GAIN)
        ),
        "n_total_configurations": int(gain.size),
        "correlation_cell_counts": {
            key: int(value)
            for key, value in frame["bounded_regime"].value_counts().items()
        },
        "tolerance": TOLERANCE,
    }
    return frame, summary


def empirical_positions() -> pd.DataFrame:
    budgets = pd.read_csv(POINT_BUDGETS)
    budgets = budgets[budgets["scope"].eq("hourly")].copy()
    budgets["rho_raw"] = budgets["raw_covariance_k2"] / np.sqrt(
        budgets["raw_core_variance_k2"] * budgets["raw_ring_variance_k2"]
    )
    budgets["rho_harmonized"] = budgets["harm_covariance_k2"] / np.sqrt(
        budgets["harm_core_variance_k2"] * budgets["harm_ring_variance_k2"]
    )
    budgets["raw_variance_scale_k2"] = (
        budgets["raw_core_variance_k2"] + budgets["raw_ring_variance_k2"]
    ) / 2.0
    budgets["core_sd_ratio"] = np.sqrt(
        budgets["harm_core_variance_k2"] / budgets["raw_core_variance_k2"]
    )
    budgets["ring_sd_ratio"] = np.sqrt(
        budgets["harm_ring_variance_k2"] / budgets["raw_ring_variance_k2"]
    )
    budgets["standardized_differential_bias_gain"] = (
        budgets["differential_bias_gain_k2"] / budgets["raw_variance_scale_k2"]
    )
    budgets["raw_core_to_ring_sd_ratio"] = np.sqrt(
        budgets["raw_core_variance_k2"] / budgets["raw_ring_variance_k2"]
    )
    budgets["gross_variance_bias_gain_k2"] = (
        budgets["component_variance_gain_k2"]
        + budgets["differential_bias_gain_k2"]
    )
    budgets["covariance_offset_fraction"] = (
        budgets["covariance_loss_penalty_k2"]
        / budgets["gross_variance_bias_gain_k2"]
    )
    budgets["reconstructed_net_gain_k2"] = (
        budgets["gross_variance_bias_gain_k2"]
        - budgets["covariance_loss_penalty_k2"]
    )
    budgets["reconstruction_residual_k2"] = (
        budgets["net_downstream_mse_gain_k2"]
        - budgets["reconstructed_net_gain_k2"]
    )
    columns = [
        "sample",
        "rho_raw",
        "rho_harmonized",
        "raw_core_to_ring_sd_ratio",
        "core_sd_ratio",
        "ring_sd_ratio",
        "standardized_differential_bias_gain",
        "gross_variance_bias_gain_k2",
        "covariance_loss_penalty_k2",
        "covariance_offset_fraction",
        "net_downstream_mse_gain_k2",
        "net_downstream_mse_gain_fraction",
        "reconstructed_net_gain_k2",
        "reconstruction_residual_k2",
    ]
    return budgets[columns].sort_values("sample").reset_index(drop=True)


def validate_outputs(
    regimes: pd.DataFrame, empirical: pd.DataFrame, summary: dict[str, object]
) -> dict[str, object]:
    fractions = regimes[
        ["fraction_downstream_gain", "fraction_downstream_damage", "fraction_boundary"]
    ].sum(axis=1)
    max_fraction_residual = float(np.abs(fractions - 1.0).max())
    max_empirical_closure = float(empirical["reconstruction_residual_k2"].abs().max())
    rho_raw = np.array([0.0, 0.47, 0.95])[:, None, None, None, None, None]
    rho_harm = np.array([0.0, 0.47, 0.95])[None, :, None, None, None, None]
    raw_ratio = RAW_CORE_TO_RING_SD_RATIO[None, None, :, None, None, None]
    raw_ring_sd = np.sqrt(2.0 / (raw_ratio**2 + 1.0))
    raw_core_sd = raw_ratio * raw_ring_sd
    q_core = CORE_SD_RATIO[None, None, None, :, None, None]
    q_ring = RING_SD_RATIO[None, None, None, None, :, None]
    bias_gain = DIFFERENTIAL_BIAS_GAIN[None, None, None, None, None, :]
    formula_gain = downstream_gain(
        rho_raw,
        rho_harm,
        raw_core_sd,
        raw_ring_sd,
        q_core,
        q_ring,
        bias_gain,
    )
    raw_bias_squared = np.maximum(bias_gain, 0.0)
    harm_bias_squared = np.maximum(-bias_gain, 0.0)
    direct_gain = (
        raw_core_sd**2
        + raw_ring_sd**2
        - 2.0 * rho_raw * raw_core_sd * raw_ring_sd
        + raw_bias_squared
        - (
            (raw_core_sd * q_core) ** 2
            + (raw_ring_sd * q_ring) ** 2
            - 2.0
            * rho_harm
            * raw_core_sd
            * raw_ring_sd
            * q_core
            * q_ring
            + harm_bias_squared
        )
    )
    max_direct_identity_residual = float(np.abs(formula_gain - direct_gain).max())
    empirical_inside_bounds = bool(
        empirical["rho_raw"].between(RHO_RAW.min(), RHO_RAW.max()).all()
        and empirical["rho_harmonized"].between(
            RHO_HARM.min(), RHO_HARM.max()
        ).all()
        and empirical["raw_core_to_ring_sd_ratio"].between(
            RAW_CORE_TO_RING_SD_RATIO.min(),
            RAW_CORE_TO_RING_SD_RATIO.max(),
        ).all()
        and empirical["core_sd_ratio"].between(
            CORE_SD_RATIO.min(), CORE_SD_RATIO.max()
        ).all()
        and empirical["ring_sd_ratio"].between(
            RING_SD_RATIO.min(), RING_SD_RATIO.max()
        ).all()
        and empirical["standardized_differential_bias_gain"].between(
            DIFFERENTIAL_BIAS_GAIN.min(), DIFFERENTIAL_BIAS_GAIN.max()
        ).all()
    )
    checks = {
        "fraction_partition_closes": max_fraction_residual < 1e-12,
        "stress_test_matches_direct_mse_difference": max_direct_identity_residual
        < 1e-12,
        "empirical_budget_reconstruction_closes": max_empirical_closure < 1e-12,
        "all_empirical_points_within_bounded_grid": empirical_inside_bounds,
        "all_three_regime_classes_present": set(regimes["bounded_regime"])
        == {"necessarily_helps", "parameter_dependent", "necessarily_damages"},
        "enumeration_count_matches_design": summary["n_total_configurations"]
        == len(RHO_RAW)
        * len(RHO_HARM)
        * len(RAW_CORE_TO_RING_SD_RATIO)
        * len(CORE_SD_RATIO)
        * len(RING_SD_RATIO)
        * len(DIFFERENTIAL_BIAS_GAIN),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise AssertionError(f"Stress-test validation failed: {failed}")
    return {
        "status": "all_checks_passed",
        "checks": checks,
        "maximum_fraction_partition_residual": max_fraction_residual,
        "maximum_direct_mse_identity_residual": max_direct_identity_residual,
        "maximum_empirical_budget_reconstruction_residual_k2": max_empirical_closure,
    }


def short_label(sample: str) -> str:
    labels = {
        "2021 external GOES17/16": "2021 external",
        "2022-2024 expansion GOES18/16": "2022–2024 expansion",
        "2025 original GOES18/19": "2025 original",
        "2025 expansion GOES18/19": "2025 expansion",
        "2026 combined GOES18/19": "2026 holdout",
    }
    return labels[sample]


def panel_label(axis: plt.Axes, label: str) -> None:
    axis.text(
        -0.11,
        1.12,
        label,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
    )


def build_figure(regimes: pd.DataFrame, empirical: pd.DataFrame) -> None:
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
            "svg.hashsalt": "gsis-covariance-regime-v1",
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.45))
    fig.subplots_adjust(
        left=0.08,
        right=0.96,
        bottom=0.18,
        top=0.95,
        wspace=0.52,
    )

    matrix = regimes.pivot(
        index="rho_harmonized",
        columns="rho_raw",
        values="fraction_downstream_gain",
    ).sort_index()
    image = axes[0].pcolormesh(
        matrix.columns,
        matrix.index,
        matrix.to_numpy(),
        shading="nearest",
        cmap="viridis",
        vmin=0,
        vmax=1,
        rasterized=True,
    )
    contour = axes[0].contour(
        matrix.columns,
        matrix.index,
        matrix.to_numpy(),
        levels=[0.01, 0.5, 0.99],
        colors=["#171717", "#171717", "#171717"],
        linewidths=[0.9, 1.15, 0.9],
        linestyles=["-", "-", "-"],
    )
    axes[0].clabel(
        contour,
        fmt={0.01: "1%", 0.5: "50%", 0.99: "99%"},
        inline=True,
        fontsize=6.6,
        colors="#171717",
    )
    for row in empirical.itertuples(index=False):
        improved = row.net_downstream_mse_gain_k2 > 0
        if improved:
            axes[0].scatter(
                row.rho_raw,
                row.rho_harmonized,
                s=24,
                marker="o",
                facecolor="#2166AC",
                edgecolor="none",
                linewidth=0,
                zorder=4,
            )
        else:
            axes[0].scatter(
                row.rho_raw,
                row.rho_harmonized,
                s=30,
                marker="x",
                color="#B2182B",
                linewidth=1.5,
                zorder=4,
            )
    terminal_ticks = [0.0, 0.2, 0.4, 0.6, 0.8, 0.95]
    axes[0].set_xlim(0, 0.95)
    axes[0].set_ylim(0, 0.95)
    axes[0].set_xticks(terminal_ticks, ["0", "0.2", "0.4", "0.6", "0.8", ""])
    axes[0].set_yticks(terminal_ticks, ["0", "0.2", "0.4", "0.6", "0.8", ""])
    axes[0].set_xlabel(r"Raw core–ring residual correlation, $\rho_{\mathrm{raw}}$")
    axes[0].set_ylabel(r"Harmonized residual correlation, $\rho_{\mathrm{harm}}$")
    axes[0].plot(
        [0, 0.95],
        [0, 0.95],
        color="#303030",
        lw=0.75,
        linestyle="--",
        zorder=3,
    )
    axes[0].text(
        0.18,
        0.205,
        "unchanged residual correlation",
        rotation=45,
        rotation_mode="anchor",
        fontsize=6.2,
        color="#303030",
        ha="left",
        va="bottom",
        zorder=5,
    )
    axes[0].legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor="#2166AC",
                markeredgecolor="none",
                markersize=4.2,
                label=r"Empirical $G_D>0$",
            ),
            Line2D(
                [0],
                [0],
                marker="x",
                linestyle="none",
                color="#B2182B",
                markeredgewidth=1.4,
                markersize=4.6,
                label=r"Empirical $G_D<0$",
            ),
        ],
        loc="upper left",
        bbox_to_anchor=(0.015, 0.985),
        frameon=False,
        borderpad=0.3,
        handletextpad=0.4,
        fontsize=6.3,
    )
    panel_label(axes[0], "a")
    colorbar = fig.colorbar(image, ax=axes[0], pad=0.015, fraction=0.048)
    colorbar.set_label(r"Deterministic proportion with $G_D>0$")

    maximum = float(
        max(
            empirical["gross_variance_bias_gain_k2"].max(),
            empirical["covariance_loss_penalty_k2"].max(),
        )
        * 1.12
    )
    axes[1].plot([0, maximum], [0, maximum], color="#242424", lw=1.0)
    axes[1].fill_between(
        [0, maximum], [0, maximum], maximum, color="#b2182b", alpha=0.08
    )
    axes[1].fill_between(
        [0, maximum], 0, [0, maximum], color="#2166ac", alpha=0.08
    )
    offsets = {
        "2021 external GOES17/16": (7, -15),
        "2022-2024 expansion GOES18/16": (-78, -1),
        "2025 original GOES18/19": (12, -18),
        "2025 expansion GOES18/19": (-54, 17),
        "2026 combined GOES18/19": (-25, -28),
    }
    for row in empirical.itertuples(index=False):
        improved = row.net_downstream_mse_gain_k2 > 0
        if improved:
            axes[1].scatter(
                row.gross_variance_bias_gain_k2,
                row.covariance_loss_penalty_k2,
                s=38,
                marker="o",
                color="#2166AC",
                edgecolor="none",
                linewidth=0,
                zorder=3,
            )
        else:
            axes[1].scatter(
                row.gross_variance_bias_gain_k2,
                row.covariance_loss_penalty_k2,
                s=46,
                marker="x",
                color="#B2182B",
                linewidth=1.6,
                zorder=3,
            )
        axes[1].annotate(
            short_label(row.sample),
            (row.gross_variance_bias_gain_k2, row.covariance_loss_penalty_k2),
            xytext=offsets[row.sample],
            textcoords="offset points",
            fontsize=6.5,
            arrowprops={"arrowstyle": "-", "lw": 0.45, "color": "#555555"},
        )
    axes[1].text(
        maximum * 0.05,
        maximum * 0.91,
        "increased downstream MSE",
        color="#8b1a1a",
        fontsize=7,
    )
    axes[1].text(
        maximum * 0.60,
        maximum * 0.08,
        "downstream gain",
        color="#174f86",
        fontsize=7,
    )
    axes[1].set(
        xlim=(0, maximum),
        ylim=(0, maximum),
        aspect="equal",
        xlabel=r"Variance + differential-bias gain (K$^2$)",
        ylabel=r"Covariance-loss penalty (K$^2$)",
    )
    panel_label(axes[1], "b")
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(direction="out", length=3, width=0.7)

    for extension in ["png", "pdf", "svg"]:
        path = FIGURES / f"covariance_regime_stress_test.{extension}"
        if extension == "pdf":
            fixed_time = datetime(2026, 8, 11, tzinfo=timezone.utc)
            metadata = {
                "Creator": "build_covariance_regime_stress_test.py",
                "CreationDate": fixed_time,
                "ModDate": fixed_time,
            }
        elif extension == "svg":
            metadata = {
                "Creator": "build_covariance_regime_stress_test.py",
                "Date": "2026-08-11",
            }
        else:
            metadata = {"Software": "build_covariance_regime_stress_test.py"}
        fig.savefig(
            path,
            dpi=400 if extension == "png" else None,
            bbox_inches="tight",
            metadata=metadata,
        )
        if extension == "svg":
            svg_text = path.read_text(encoding="utf-8")
            path.write_text(
                "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
                encoding="utf-8",
            )
    plt.close(fig)


def write_caption() -> None:
    caption = r"""**Figure 3. Deterministic covariance-regime stress test and empirical cohort positions.** \(G_D\) is raw-minus-component-harmonized downstream mean-squared-error (MSE) gain, and \(G_D>0\) indicates improved downstream agreement. **(a)** Deterministic proportion of the bounded parameter grid for which \(G_D>0\). Raw and harmonized core/ring residual correlations range from 0 to 0.95; component residual-scale ratios and differential-bias gains are enumerated exactly. Dark contours mark deterministic proportions of 1%, 50%, and 99%, and the dashed identity line marks unchanged residual correlation, \(\rho_{\mathrm{harm}}=\rho_{\mathrm{raw}}\). Filled blue circles denote empirical cohorts with positive downstream MSE gain and red crosses denote negative gain. **(b)** Empirical covariance-loss penalty against gross component-variance plus differential-bias gain. The diagonal is the exact \(G_D=0\) boundary; points below it improve downstream agreement and points above it increase downstream MSE. The test is a deterministic enumeration, not a probability model, and uses no random sampling or new satellite observations.
"""
    (FIGURES / "covariance_regime_stress_test_caption.md").write_text(
        caption, encoding="utf-8"
    )


def write_artifact_hashes() -> None:
    paths = [
        Path(__file__),
        POINT_BUDGETS,
        SIMULATION / "README.md",
        SIMULATION / "covariance_regime_grid.csv",
        SIMULATION / "empirical_cohort_positions.csv",
        SIMULATION / "covariance_regime_simulation_summary.json",
        SIMULATION / "covariance_regime_validation.json",
        FIGURES / "covariance_regime_stress_test.png",
        FIGURES / "covariance_regime_stress_test.pdf",
        FIGURES / "covariance_regime_stress_test.svg",
        FIGURES / "covariance_regime_stress_test_caption.md",
    ]
    hashes = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in paths
    }
    (SIMULATION / "simulation_artifact_hashes.json").write_text(
        json.dumps(hashes, indent=2), encoding="utf-8"
    )


def main() -> None:
    SIMULATION.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    regimes, summary = enumerate_regimes()
    empirical = empirical_positions()
    validation = validate_outputs(regimes, empirical, summary)
    summary["validation"] = validation
    summary["frozen_point_budget_sha256"] = sha256(POINT_BUDGETS)

    regimes.to_csv(SIMULATION / "covariance_regime_grid.csv", index=False)
    empirical.to_csv(SIMULATION / "empirical_cohort_positions.csv", index=False)
    (SIMULATION / "covariance_regime_simulation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (SIMULATION / "covariance_regime_validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    build_figure(regimes, empirical)
    write_caption()
    write_artifact_hashes()
    print(json.dumps({**summary, "bounds": "see output JSON"}, indent=2))


if __name__ == "__main__":
    main()
