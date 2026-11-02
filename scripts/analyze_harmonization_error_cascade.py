from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

from run_multiplatform_harmonization import ccc, transition_frame


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/grl_deepening_2026/harmonization_error_cascade"
METRIC_OUT = ROOT / "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization"
EXP_OUT = ROOT / "outputs/grl_deepening_2026/multiplatform_expanded_validation"
FIRST_OUT = ROOT / "outputs/grl_deepening_2026/multiplatform_harmonization"
SEED = 20260810


def rmse(values: np.ndarray, weights: np.ndarray | None = None) -> float:
    values = np.asarray(values, dtype=float)
    if weights is None:
        return float(np.sqrt(np.mean(values**2)))
    return float(np.sqrt(np.average(values**2, weights=weights)))


def weighted_covariance(x: np.ndarray, y: np.ndarray, weights: np.ndarray) -> float:
    mean_x = np.average(x, weights=weights)
    mean_y = np.average(y, weights=weights)
    return float(np.average((x - mean_x) * (y - mean_y), weights=weights))


def decomposition(
    frame: pd.DataFrame,
    core_estimate: str,
    ring_estimate: str,
    model: str,
    weights: np.ndarray | None = None,
) -> dict[str, float]:
    core_error = (frame[core_estimate] - frame["target_core"]).to_numpy(dtype=float)
    ring_error = (frame[ring_estimate] - frame["target_ring"]).to_numpy(dtype=float)
    anomaly_error = core_error - ring_error
    if weights is None:
        weights = np.ones(len(frame))
    var_core = weighted_covariance(core_error, core_error, weights)
    var_ring = weighted_covariance(ring_error, ring_error, weights)
    covariance = weighted_covariance(core_error, ring_error, weights)
    correlation = covariance / np.sqrt(var_core * var_ring)
    common_mode_fraction = 2 * covariance / (var_core + var_ring)
    return {
        "model": model,
        "core_rmse_k": rmse(core_error, weights),
        "ring_rmse_k": rmse(ring_error, weights),
        "component_mean_rmse_k": (rmse(core_error, weights) + rmse(ring_error, weights)) / 2,
        "anomaly_rmse_k": rmse(anomaly_error, weights),
        "core_error_variance": var_core,
        "ring_error_variance": var_ring,
        "core_ring_error_covariance": covariance,
        "core_ring_error_correlation": correlation,
        "common_mode_cancellation_fraction": common_mode_fraction,
        "anomaly_error_variance": weighted_covariance(anomaly_error, anomaly_error, weights),
        "anomaly_variance_from_identity": var_core + var_ring - 2 * covariance,
    }


def crossed_bootstrap(frame: pd.DataFrame, draws: int = 5000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    cities = np.array(sorted(frame["uc_id"].unique()))
    events = np.array(sorted(frame["event_time_id"].unique()))
    rows = []
    for iteration in range(draws):
        city_counts = pd.Series(rng.choice(cities, len(cities), replace=True)).value_counts()
        event_counts = pd.Series(rng.choice(events, len(events), replace=True)).value_counts()
        weights = (
            frame["uc_id"].map(city_counts).fillna(0).to_numpy()
            * frame["event_time_id"].map(event_counts).fillna(0).to_numpy()
        )
        if weights.sum() == 0:
            continue
        raw = decomposition(frame, "source_core", "source_ring", "raw", weights)
        corrected = decomposition(
            frame, "metric_pred_core", "metric_pred_ring", "corrected", weights
        )
        rows.append(
            {
                "iteration": iteration,
                "core_rmse_reduction_fraction": 1
                - corrected["core_rmse_k"] / raw["core_rmse_k"],
                "ring_rmse_reduction_fraction": 1
                - corrected["ring_rmse_k"] / raw["ring_rmse_k"],
                "anomaly_rmse_reduction_fraction": 1
                - corrected["anomaly_rmse_k"] / raw["anomaly_rmse_k"],
                "error_correlation_change": corrected[
                    "core_ring_error_correlation"
                ]
                - raw["core_ring_error_correlation"],
                "common_mode_cancellation_change": corrected[
                    "common_mode_cancellation_fraction"
                ]
                - raw["common_mode_cancellation_fraction"],
                "anomaly_variance_change": corrected["anomaly_error_variance"]
                - raw["anomaly_error_variance"],
            }
        )
    return pd.DataFrame(rows)


def bootstrap_summary(bootstrap: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in bootstrap.columns:
        if column == "iteration":
            continue
        rows.append(
            {
                "metric": column,
                "estimate": bootstrap[column].mean(),
                "ci95_low": bootstrap[column].quantile(0.025),
                "ci95_high": bootstrap[column].quantile(0.975),
                "probability_gt_zero": (bootstrap[column] > 0).mean(),
            }
        )
    return pd.DataFrame(rows)


def stratified(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    city = data.groupby("uc_id", observed=True).agg(
        mean_vza=("vza_source", "mean"),
        lon=("lon", "first"),
        cohort=("calibration_cohort", "first"),
    )
    city["vza_quartile"] = pd.qcut(
        city["mean_vza"].rank(method="first"), 4, labels=False
    ) + 1
    city["longitude_quartile"] = pd.qcut(
        city["lon"].rank(method="first"), 4, labels=False
    ) + 1
    data = data.merge(
        city[["vza_quartile", "longitude_quartile"]],
        left_on="uc_id",
        right_index=True,
        validate="many_to_one",
    )
    rows = []
    groupings = {
        "combined": pd.Series("all", index=data.index),
        "cohort": data["calibration_cohort"],
        "vza_quartile": data["vza_quartile"],
        "longitude_quartile": data["longitude_quartile"],
        "event": data["event_time_id"],
    }
    for name, labels in groupings.items():
        for level, subset in data.groupby(labels, observed=True):
            raw = decomposition(subset, "source_core", "source_ring", "raw")
            corrected = decomposition(
                subset, "metric_pred_core", "metric_pred_ring", "corrected"
            )
            for result in [raw, corrected]:
                rows.append(
                    {
                        "stratifier": name,
                        "stratum": str(level),
                        "n_hourly": len(subset),
                        "n_cities": subset["uc_id"].nunique(),
                        "n_events": subset["event_time_id"].nunique(),
                        **result,
                    }
                )
    return pd.DataFrame(rows)


def clopper_pearson(successes: int, total: int, alpha: float = 0.05) -> tuple[float, float]:
    if total == 0:
        return np.nan, np.nan
    low = 0.0 if successes == 0 else beta.ppf(alpha / 2, successes, total - successes + 1)
    high = 1.0 if successes == total else beta.ppf(1 - alpha / 2, successes + 1, total - successes)
    return float(low), float(high)


def uncertainty_intervals(transitions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    groups = [("combined", transitions)] + list(
        transitions.groupby("calibration_cohort", observed=True)
    )
    for label, frame in groups:
        covered = int(frame["covered"].sum())
        n = len(frame)
        coverage_low, coverage_high = clopper_pearson(covered, n)
        certified = frame[frame["certified_sign"].ne(0)]
        correct = int(certified["certified_correct"].sum())
        sign_low, sign_high = clopper_pearson(correct, len(certified))
        rows.append(
            {
                "cohort": label,
                "n": n,
                "coverage": covered / n,
                "coverage_ci95_low": coverage_low,
                "coverage_ci95_high": coverage_high,
                "n_certified": len(certified),
                "certified_fraction": len(certified) / n,
                "certified_sign_accuracy": correct / len(certified)
                if len(certified)
                else np.nan,
                "sign_accuracy_ci95_low": sign_low,
                "sign_accuracy_ci95_high": sign_high,
            }
        )
    return pd.DataFrame(rows)


def period_summary() -> pd.DataFrame:
    rows = []
    sources = [
        (
            "2022-2024 expansion GOES18/16",
            EXP_OUT / "historical_expanded_metrics.csv",
        ),
        ("2025 original GOES18/19", FIRST_OUT / "validation_2025_metrics.csv"),
        (
            "2025 expansion GOES18/19",
            EXP_OUT / "validation_expanded_metrics.csv",
        ),
        ("2026 combined GOES18/19", METRIC_OUT / "validation_2026_metrics.csv"),
    ]
    for label, path in sources:
        frame = pd.read_csv(path)
        if label.startswith("2026"):
            raw = frame[
                frame["scope"].eq("hourly") & frame["model"].eq("raw")
            ].set_index("component")
            metric_aware = frame[
                frame["scope"].eq("hourly")
                & frame["model"].eq("metric_aware")
            ].set_index("component")
            component_derived = frame[
                frame["scope"].eq("hourly")
                & frame["model"].eq("component_derived")
            ].set_index("component")
        else:
            raw = frame[frame["model"].eq("raw") & frame["scope"].eq("hourly")].set_index("component")
            corrected = frame[
                frame["model"].eq("corrected") & frame["scope"].eq("hourly")
            ].set_index("component")
        for component in ["core", "ring", "anomaly"]:
            if label.startswith("2026"):
                corrected_row = (
                    component_derived.loc[component]
                    if component == "anomaly"
                    else metric_aware.loc[component]
                )
            else:
                corrected_row = corrected.loc[component]
            rows.append(
                {
                    "sample": label,
                    "component": component,
                    "raw_rmse_k": raw.loc[component, "rmse_k"],
                    "corrected_rmse_k": corrected_row["rmse_k"],
                    "rmse_reduction_fraction": 1
                    - corrected_row["rmse_k"] / raw.loc[component, "rmse_k"],
                }
            )
    return pd.DataFrame(rows)


def cross_sample_decomposition() -> pd.DataFrame:
    sources = [
        (
            "2022-2024 expansion GOES18/16",
            EXP_OUT / "historical_expanded_predictions.parquet",
            "pred_core",
            "pred_ring",
        ),
        (
            "2025 original GOES18/19",
            FIRST_OUT / "validation_2025_predictions.parquet",
            "pred_core",
            "pred_ring",
        ),
        (
            "2025 expansion GOES18/19",
            EXP_OUT / "validation_expanded_predictions.parquet",
            "pred_core",
            "pred_ring",
        ),
        (
            "2026 combined GOES18/19",
            METRIC_OUT / "validation_2026_hourly_predictions.parquet",
            "metric_pred_core",
            "metric_pred_ring",
        ),
    ]
    rows = []
    for sample, path, core_estimate, ring_estimate in sources:
        frame = pd.read_parquet(path)
        for result in [
            decomposition(frame, "source_core", "source_ring", "raw"),
            decomposition(frame, core_estimate, ring_estimate, "component_corrected"),
        ]:
            rows.append(
                {
                    "sample": sample,
                    "n_hourly": len(frame),
                    "n_cities": frame["uc_id"].nunique(),
                    "n_events": frame["event_time_id"].nunique(),
                    **result,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hourly = pd.read_parquet(METRIC_OUT / "validation_2026_hourly_predictions.parquet")
    transitions = pd.read_parquet(
        METRIC_OUT / "validation_2026_transition_predictions.parquet"
    )
    overall = pd.DataFrame(
        [
            decomposition(hourly, "source_core", "source_ring", "raw"),
            decomposition(
                hourly, "metric_pred_core", "metric_pred_ring", "corrected"
            ),
        ]
    )
    bootstrap = crossed_bootstrap(hourly)
    summary = bootstrap_summary(bootstrap)
    strata = stratified(hourly)
    uncertainty = uncertainty_intervals(transitions)
    periods = period_summary()
    samples = cross_sample_decomposition()
    overall.to_csv(OUT / "error_decomposition_overall.csv", index=False)
    bootstrap.to_parquet(OUT / "error_decomposition_crossed_bootstrap.parquet", index=False)
    summary.to_csv(OUT / "error_decomposition_bootstrap_summary.csv", index=False)
    strata.to_csv(OUT / "error_decomposition_stratified.csv", index=False)
    uncertainty.to_csv(OUT / "uncertainty_exact_intervals.csv", index=False)
    periods.to_csv(OUT / "cross_sample_rmse_summary.csv", index=False)
    samples.to_csv(OUT / "cross_sample_error_decomposition.csv", index=False)
    raw = overall.set_index("model").loc["raw"]
    corrected = overall.set_index("model").loc["corrected"]
    report = {
        "finding": "component calibration reduces absolute LST error but loses common-mode cancellation in the derived spatial difference",
        "n_hourly": int(len(hourly)),
        "n_cities": int(hourly["uc_id"].nunique()),
        "n_events": int(hourly["event_time_id"].nunique()),
        "core_rmse_reduction_fraction": float(
            1 - corrected["core_rmse_k"] / raw["core_rmse_k"]
        ),
        "ring_rmse_reduction_fraction": float(
            1 - corrected["ring_rmse_k"] / raw["ring_rmse_k"]
        ),
        "component_derived_anomaly_rmse_reduction_fraction": float(
            1 - corrected["anomaly_rmse_k"] / raw["anomaly_rmse_k"]
        ),
        "raw_error_correlation": float(raw["core_ring_error_correlation"]),
        "corrected_error_correlation": float(
            corrected["core_ring_error_correlation"]
        ),
        "raw_common_mode_cancellation_fraction": float(
            raw["common_mode_cancellation_fraction"]
        ),
        "corrected_common_mode_cancellation_fraction": float(
            corrected["common_mode_cancellation_fraction"]
        ),
        "bootstrap": summary.to_dict(orient="records"),
        "uncertainty": uncertainty.to_dict(orient="records"),
    }
    (OUT / "error_cascade_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
