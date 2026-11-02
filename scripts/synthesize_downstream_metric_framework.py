from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs/grl_deepening_2026"
OUT = BASE / "downstream_metric_framework"
CASCADE = BASE / "harmonization_error_cascade"
EXTERNAL = BASE / "goes17_goes16_external_metric"


def main() -> None:
    budgets = pd.read_csv(OUT / "exact_mse_budgets_all_samples.csv")
    external = pd.read_csv(EXTERNAL / "validation_2021_exact_mse_budget.csv")
    external["sample"] = "2021 external GOES17/16"
    columns = list(dict.fromkeys([*budgets.columns, *external.columns]))
    combined = pd.concat(
        [
            budgets.reindex(columns=columns),
            external.reindex(columns=columns),
        ],
        ignore_index=True,
    )
    combined.to_csv(OUT / "exact_mse_budgets_with_external.csv", index=False)

    rmse = pd.read_csv(CASCADE / "cross_sample_rmse_summary.csv")
    external_hourly = external[external["scope"].eq("hourly")].iloc[0]
    external_rmse = pd.DataFrame(
        [
            {
                "sample": "2021 external GOES17/16",
                "component": component,
                "raw_rmse_k": external_hourly[f"raw_{component}_rmse_k"],
                "corrected_rmse_k": external_hourly[f"harm_{component}_rmse_k"],
                "rmse_reduction_fraction": external_hourly[
                    f"{component}_rmse_reduction_fraction"
                ],
            }
            for component in ["core", "ring", "anomaly"]
        ]
    )
    rmse = pd.concat([external_rmse, rmse], ignore_index=True)
    rmse.to_csv(OUT / "cross_sample_rmse_with_external.csv", index=False)

    hourly = combined[combined["scope"].eq("hourly")].copy()
    hourly["gross_variance_bias_gain_k2"] = (
        hourly["component_variance_gain_k2"]
        + hourly["differential_bias_gain_k2"]
    )
    hourly["covariance_offset_fraction"] = (
        hourly["covariance_loss_penalty_k2"]
        / hourly["gross_variance_bias_gain_k2"]
    )
    components = rmse[rmse["component"].isin(["core", "ring"])]
    anomaly = rmse[rmse["component"].eq("anomaly")]

    external_bootstrap = pd.read_csv(
        EXTERNAL / "validation_2021_bootstrap_summary.csv"
    )
    external_hourly_bootstrap = external_bootstrap[
        external_bootstrap["scope"].eq("hourly")
    ].set_index("metric")
    uncertainty = pd.read_csv(CASCADE / "uncertainty_exact_intervals.csv")
    combined_uncertainty = uncertainty[uncertainty["cohort"].eq("combined")].iloc[0]
    decisions = pd.read_csv(OUT / "metric_aware_decision_audit.csv")

    summary = {
        "status": "complete",
        "n_out_of_sample_evaluation_cohorts": int(hourly["sample"].nunique()),
        "platform_pairings": ["GOES17/16", "GOES18/16", "GOES18/19"],
        "period_covered": "2019-2026",
        "component_results": {
            "all_core_and_ring_rmse_reductions_positive": bool(
                (components["rmse_reduction_fraction"] > 0).all()
            ),
            "minimum_component_rmse_reduction_fraction": float(
                components["rmse_reduction_fraction"].min()
            ),
            "maximum_component_rmse_reduction_fraction": float(
                components["rmse_reduction_fraction"].max()
            ),
        },
        "downstream_results": {
            "minimum_anomaly_rmse_reduction_fraction": float(
                anomaly["rmse_reduction_fraction"].min()
            ),
            "maximum_anomaly_rmse_reduction_fraction": float(
                anomaly["rmse_reduction_fraction"].max()
            ),
            "samples_with_anomaly_point_improvement": int(
                (anomaly["rmse_reduction_fraction"] > 0).sum()
            ),
            "samples_with_anomaly_point_deterioration_or_no_gain": int(
                (anomaly["rmse_reduction_fraction"] <= 0).sum()
            ),
        },
        "mse_budget": {
            "all_hourly_covariance_loss_penalties_positive": bool(
                (hourly["covariance_loss_penalty_k2"] > 0).all()
            ),
            "covariance_offset_fraction_min": float(
                hourly["covariance_offset_fraction"].min()
            ),
            "covariance_offset_fraction_max": float(
                hourly["covariance_offset_fraction"].max()
            ),
            "maximum_absolute_closure_residual_k2": float(
                combined["budget_closure_residual_k2"].abs().max()
            ),
        },
        "external_2021": {
            "n_hourly": int(external_hourly["n"]),
            "n_cities": int(external_hourly["n_cities"]),
            "n_events": int(external_hourly["n_events"]),
            "core_rmse_reduction_fraction": float(
                external_hourly["core_rmse_reduction_fraction"]
            ),
            "ring_rmse_reduction_fraction": float(
                external_hourly["ring_rmse_reduction_fraction"]
            ),
            "anomaly_rmse_reduction_fraction": float(
                external_hourly["anomaly_rmse_reduction_fraction"]
            ),
            "raw_error_correlation": float(
                external_hourly["raw_error_correlation"]
            ),
            "harm_error_correlation": float(
                external_hourly["harm_error_correlation"]
            ),
            "component_variance_gain_k2": float(
                external_hourly["component_variance_gain_k2"]
            ),
            "differential_bias_gain_k2": float(
                external_hourly["differential_bias_gain_k2"]
            ),
            "covariance_loss_penalty_k2": float(
                external_hourly["covariance_loss_penalty_k2"]
            ),
            "net_downstream_mse_gain_k2": float(
                external_hourly["net_downstream_mse_gain_k2"]
            ),
            "bootstrap_ci95": {
                metric: {
                    "low": float(external_hourly_bootstrap.loc[metric, "ci95_low"]),
                    "high": float(
                        external_hourly_bootstrap.loc[metric, "ci95_high"]
                    ),
                }
                for metric in [
                    "core_rmse_reduction_fraction",
                    "ring_rmse_reduction_fraction",
                    "anomaly_rmse_reduction_fraction",
                    "covariance_loss_penalty_k2",
                    "net_downstream_mse_gain_k2",
                ]
            },
        },
        "uncertainty_gate_2026": {
            "n": int(combined_uncertainty["n"]),
            "coverage": float(combined_uncertainty["coverage"]),
            "certified_fraction": float(
                combined_uncertainty["certified_fraction"]
            ),
            "certified_sign_accuracy": float(
                combined_uncertainty["certified_sign_accuracy"]
            ),
        },
        "decision_actions": decisions[
            [
                "measurement_level",
                "measurand",
                "calibration_decision",
                "operational_action",
            ]
        ].to_dict(orient="records"),
    }
    (OUT / "downstream_metric_framework_synthesis.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
