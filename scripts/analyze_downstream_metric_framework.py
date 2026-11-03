from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_multiplatform_harmonization import transition_frame


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs/grl_deepening_2026"
OUT = BASE / "downstream_metric_framework"
FIRST = BASE / "multiplatform_harmonization"
EXPANDED = BASE / "multiplatform_expanded_validation"
METRIC = BASE / "goes18_goes19_metric_harmonization"
CASCADE = BASE / "harmonization_error_cascade"
SEED = 20260810
BOOTSTRAP_DRAWS = 5000


def prepare_frame(
    path: Path, core_estimate: str, ring_estimate: str
) -> pd.DataFrame:
    frame = pd.read_parquet(path).copy()
    frame["pred_core"] = frame[core_estimate]
    frame["pred_ring"] = frame[ring_estimate]
    frame["pred_anomaly"] = frame["pred_core"] - frame["pred_ring"]
    return frame


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.average(values, weights=weights))


def weighted_variance(values: np.ndarray, weights: np.ndarray) -> float:
    mean = weighted_mean(values, weights)
    return float(np.average((values - mean) ** 2, weights=weights))


def weighted_covariance(
    left: np.ndarray, right: np.ndarray, weights: np.ndarray
) -> float:
    left_mean = weighted_mean(left, weights)
    right_mean = weighted_mean(right, weights)
    return float(
        np.average((left - left_mean) * (right - right_mean), weights=weights)
    )


def mse_budget(
    frame: pd.DataFrame,
    scope: str,
    weights: np.ndarray | None = None,
) -> dict[str, float]:
    suffix = "" if scope == "hourly" else "_transition"
    raw_core = (
        frame[f"source_core{suffix}"] - frame[f"target_core{suffix}"]
    ).to_numpy(dtype=float)
    raw_ring = (
        frame[f"source_ring{suffix}"] - frame[f"target_ring{suffix}"]
    ).to_numpy(dtype=float)
    harm_core = (
        frame[f"pred_core{suffix}"] - frame[f"target_core{suffix}"]
    ).to_numpy(dtype=float)
    harm_ring = (
        frame[f"pred_ring{suffix}"] - frame[f"target_ring{suffix}"]
    ).to_numpy(dtype=float)
    if weights is None:
        weights = np.ones(len(frame), dtype=float)
    else:
        weights = np.asarray(weights, dtype=float)

    def moments(core: np.ndarray, ring: np.ndarray) -> dict[str, float]:
        core_bias = weighted_mean(core, weights)
        ring_bias = weighted_mean(ring, weights)
        core_variance = weighted_variance(core, weights)
        ring_variance = weighted_variance(ring, weights)
        covariance = weighted_covariance(core, ring, weights)
        differential_bias_squared = (core_bias - ring_bias) ** 2
        derived = core - ring
        derived_mse = float(np.average(derived**2, weights=weights))
        identity_mse = (
            core_variance
            + ring_variance
            - 2 * covariance
            + differential_bias_squared
        )
        return {
            "core_bias_k": core_bias,
            "ring_bias_k": ring_bias,
            "core_variance_k2": core_variance,
            "ring_variance_k2": ring_variance,
            "core_ring_covariance_k2": covariance,
            "differential_bias_squared_k2": differential_bias_squared,
            "derived_mse_k2": derived_mse,
            "identity_mse_k2": identity_mse,
            "identity_residual_k2": derived_mse - identity_mse,
        }

    raw = moments(raw_core, raw_ring)
    harm = moments(harm_core, harm_ring)
    variance_gain = (
        raw["core_variance_k2"]
        - harm["core_variance_k2"]
        + raw["ring_variance_k2"]
        - harm["ring_variance_k2"]
    )
    bias_gain = (
        raw["differential_bias_squared_k2"]
        - harm["differential_bias_squared_k2"]
    )
    covariance_penalty = 2 * (
        raw["core_ring_covariance_k2"]
        - harm["core_ring_covariance_k2"]
    )
    net_gain = raw["derived_mse_k2"] - harm["derived_mse_k2"]
    budget_sum = variance_gain + bias_gain - covariance_penalty
    return {
        "scope": scope,
        "n": int(len(frame)),
        "raw_core_bias_k": raw["core_bias_k"],
        "raw_ring_bias_k": raw["ring_bias_k"],
        "harm_core_bias_k": harm["core_bias_k"],
        "harm_ring_bias_k": harm["ring_bias_k"],
        "raw_core_variance_k2": raw["core_variance_k2"],
        "raw_ring_variance_k2": raw["ring_variance_k2"],
        "harm_core_variance_k2": harm["core_variance_k2"],
        "harm_ring_variance_k2": harm["ring_variance_k2"],
        "raw_covariance_k2": raw["core_ring_covariance_k2"],
        "harm_covariance_k2": harm["core_ring_covariance_k2"],
        "raw_differential_bias_squared_k2": raw[
            "differential_bias_squared_k2"
        ],
        "harm_differential_bias_squared_k2": harm[
            "differential_bias_squared_k2"
        ],
        "raw_downstream_mse_k2": raw["derived_mse_k2"],
        "harm_downstream_mse_k2": harm["derived_mse_k2"],
        "component_variance_gain_k2": variance_gain,
        "differential_bias_gain_k2": bias_gain,
        "covariance_loss_penalty_k2": covariance_penalty,
        "net_downstream_mse_gain_k2": net_gain,
        "net_downstream_mse_gain_fraction": (
            net_gain / raw["derived_mse_k2"]
            if raw["derived_mse_k2"] > 0
            else np.nan
        ),
        "budget_sum_k2": budget_sum,
        "budget_closure_residual_k2": net_gain - budget_sum,
        "raw_identity_residual_k2": raw["identity_residual_k2"],
        "harm_identity_residual_k2": harm["identity_residual_k2"],
    }


def sample_frames() -> dict[str, pd.DataFrame]:
    return {
        "2022-2024 expansion GOES18/16": prepare_frame(
            EXPANDED / "historical_expanded_predictions.parquet",
            "pred_core",
            "pred_ring",
        ),
        "2025 original GOES18/19": prepare_frame(
            FIRST / "validation_2025_predictions.parquet",
            "pred_core",
            "pred_ring",
        ),
        "2025 expansion GOES18/19": prepare_frame(
            EXPANDED / "validation_expanded_predictions.parquet",
            "pred_core",
            "pred_ring",
        ),
        "2026 combined GOES18/19": prepare_frame(
            METRIC / "validation_2026_hourly_predictions.parquet",
            "metric_pred_core",
            "metric_pred_ring",
        ),
    }


def point_budgets(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for sample, hourly in frames.items():
        transitions = transition_frame(hourly)
        for scope, frame in [("hourly", hourly), ("transition", transitions)]:
            rows.append(
                {
                    "sample": sample,
                    "n_cities": int(frame["uc_id"].nunique()),
                    "n_events": int(frame["event_time_id"].nunique()),
                    **mse_budget(frame, scope),
                }
            )
    return pd.DataFrame(rows)


def crossed_bootstrap(
    hourly: pd.DataFrame, draws: int = BOOTSTRAP_DRAWS
) -> pd.DataFrame:
    transitions = transition_frame(hourly)
    rng = np.random.default_rng(SEED)
    rows = []
    for iteration in range(draws):
        cities = np.array(sorted(hourly["uc_id"].unique()))
        events = np.array(sorted(hourly["event_time_id"].unique()))
        city_counts = pd.Series(
            rng.choice(cities, len(cities), replace=True)
        ).value_counts()
        event_counts = pd.Series(
            rng.choice(events, len(events), replace=True)
        ).value_counts()
        for scope, frame in [("hourly", hourly), ("transition", transitions)]:
            weights = (
                frame["uc_id"].map(city_counts).fillna(0).to_numpy(dtype=float)
                * frame["event_time_id"]
                .map(event_counts)
                .fillna(0)
                .to_numpy(dtype=float)
            )
            if weights.sum() == 0:
                continue
            rows.append(
                {
                    "iteration": iteration,
                    **mse_budget(frame, scope, weights),
                }
            )
    return pd.DataFrame(rows)


def summarize_bootstrap(bootstrap: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "component_variance_gain_k2",
        "differential_bias_gain_k2",
        "covariance_loss_penalty_k2",
        "net_downstream_mse_gain_k2",
        "net_downstream_mse_gain_fraction",
        "budget_closure_residual_k2",
    ]
    rows = []
    for scope, frame in bootstrap.groupby("scope", observed=True):
        for metric in metrics:
            rows.append(
                {
                    "scope": scope,
                    "metric": metric,
                    "estimate": float(frame[metric].mean()),
                    "ci95_low": float(frame[metric].quantile(0.025)),
                    "ci95_high": float(frame[metric].quantile(0.975)),
                    "probability_gt_zero": float((frame[metric] > 0).mean()),
                    "n_bootstrap": int(frame["iteration"].nunique()),
                }
            )
    return pd.DataFrame(rows)


def decision_audit() -> pd.DataFrame:
    manifest = json.loads(
        (METRIC / "frozen_metric_aware_manifest.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        (METRIC / "validation_2026_report.json").read_text(encoding="utf-8")
    )
    uncertainty = pd.read_csv(CASCADE / "uncertainty_exact_intervals.csv").set_index(
        "cohort"
    )
    selected = manifest["selected_hourly_models"]
    return pd.DataFrame(
        [
            {
                "measurement_level": "component",
                "measurand": "hourly urban-core LST",
                "calibration_decision": selected["core"],
                "operational_action": "use component correction",
                "independent_2026_result": validation["rmse_reduction_fraction"][
                    "core_hourly"
                ],
                "result_unit": "RMSE reduction fraction",
            },
            {
                "measurement_level": "component",
                "measurand": "hourly surrounding-ring LST",
                "calibration_decision": selected["ring"],
                "operational_action": "use component correction",
                "independent_2026_result": validation["rmse_reduction_fraction"][
                    "ring_hourly"
                ],
                "result_unit": "RMSE reduction fraction",
            },
            {
                "measurement_level": "spatial contrast",
                "measurand": "hourly core-minus-ring LST",
                "calibration_decision": selected["anomaly"],
                "operational_action": "retain raw downstream metric",
                "independent_2026_result": validation["rmse_reduction_fraction"][
                    "anomaly_hourly"
                ],
                "result_unit": "direct RMSE reduction fraction",
            },
            {
                "measurement_level": "temporal transition",
                "measurand": "pre-to-post-sunset core-minus-ring transition",
                "calibration_decision": manifest["selected_transition_model"],
                "operational_action": "retain raw downstream metric",
                "independent_2026_result": validation["rmse_reduction_fraction"][
                    "anomaly_transition"
                ],
                "result_unit": "direct RMSE reduction fraction",
            },
            {
                "measurement_level": "directional inference",
                "measurand": "sign of core-minus-ring transition",
                "calibration_decision": "frozen uncertainty gate",
                "operational_action": "certify or abstain",
                "independent_2026_result": uncertainty.loc[
                    "combined", "certified_sign_accuracy"
                ],
                "result_unit": "accuracy among certified signs",
            },
        ]
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = sample_frames()
    points = point_budgets(frames)
    points.to_csv(OUT / "exact_mse_budgets_all_samples.csv", index=False)

    bootstrap = crossed_bootstrap(frames["2026 combined GOES18/19"])
    bootstrap.to_parquet(OUT / "mse_budget_2026_crossed_bootstrap.parquet", index=False)
    summary = summarize_bootstrap(bootstrap)
    summary.to_csv(OUT / "mse_budget_2026_bootstrap_summary.csv", index=False)

    decisions = decision_audit()
    decisions.to_csv(OUT / "metric_aware_decision_audit.csv", index=False)

    max_closure = float(points["budget_closure_residual_k2"].abs().max())
    max_identity = float(
        points[["raw_identity_residual_k2", "harm_identity_residual_k2"]]
        .abs()
        .to_numpy()
        .max()
    )
    report = {
        "status": "complete",
        "protocol": str(ROOT / "downstream_metric_aware_harmonization_protocol.md"),
        "n_samples": int(points["sample"].nunique()),
        "scopes": sorted(points["scope"].unique().tolist()),
        "max_point_budget_closure_residual_k2": max_closure,
        "max_point_identity_residual_k2": max_identity,
        "prospective_2026": points[
            points["sample"].eq("2026 combined GOES18/19")
        ].to_dict(orient="records"),
        "decisions": decisions.to_dict(orient="records"),
    }
    (OUT / "downstream_metric_framework_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
