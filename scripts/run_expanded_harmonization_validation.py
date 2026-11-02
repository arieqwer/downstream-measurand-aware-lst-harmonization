from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from run_multiplatform_harmonization import (
    MODEL_PATH,
    OUT as BASE_OUT,
    aggregate_pair,
    apply_models,
    bootstrap_primary,
    leave_one_event_out,
    metric_rows,
    transition_frame,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/grl_deepening_2026/multiplatform_expanded_validation"

DEFINITIONS = {
    "historical": {
        "name": "expansion_goes18_minus_goes16",
        "sensor_a": "GOES18",
        "sensor_b": "GOES16",
        "hourly_a": ROOT
        / "outputs/goes18_2022_2024_expansion/goes_sunset_hourly_analysis.parquet",
        "hourly_b": ROOT
        / "outputs/goes16_2018_2024_low_green/goes_sunset_hourly_analysis.parquet",
        "cities": ROOT / "data/goes18_2022_2024_expansion/goes_sunset_cities.csv",
        "bucket_a": "noaa-goes18",
        "bucket_b": "noaa-goes16",
        "period": "expansion_historical_2022_2024",
    },
    "validation": {
        "name": "expansion_goes18_minus_goes19",
        "sensor_a": "GOES18",
        "sensor_b": "GOES19",
        "hourly_a": ROOT
        / "outputs/goes18_2025_expansion/goes_sunset_hourly_analysis.parquet",
        "hourly_b": ROOT
        / "outputs/goes19_2025_low_green/goes_sunset_hourly_analysis.parquet",
        "cities": ROOT / "data/goes18_2025_expansion/goes_sunset_cities.csv",
        "bucket_a": "noaa-goes18",
        "bucket_b": "noaa-goes19",
        "period": "expansion_validation_2025",
    },
}


def comparison_metrics(frame: pd.DataFrame, cohort: str) -> pd.DataFrame:
    metrics = pd.concat(
        [
            metric_rows(frame, "source", "raw"),
            metric_rows(frame, "pred", "corrected"),
        ],
        ignore_index=True,
    )
    metrics["cohort"] = cohort
    raw = metrics[metrics["model"].eq("raw")].set_index(["scope", "component"])
    corrected = metrics[metrics["model"].eq("corrected")].set_index(
        ["scope", "component"]
    )
    for index in corrected.index:
        metrics.loc[
            metrics["model"].eq("corrected")
            & metrics["scope"].eq(index[0])
            & metrics["component"].eq(index[1]),
            "rmse_reduction_fraction",
        ] = 1 - corrected.loc[index, "rmse_k"] / raw.loc[index, "rmse_k"]
    return metrics


def stratified_metrics(frame: pd.DataFrame, cohort: str) -> pd.DataFrame:
    data = frame.copy()
    city_vza = data.groupby("uc_id")["vza_source"].mean()
    city_lon = data.groupby("uc_id")["lon"].first()
    vza_group = pd.qcut(city_vza.rank(method="first"), 4, labels=False) + 1
    lon_group = pd.qcut(city_lon.rank(method="first"), 4, labels=False) + 1
    data["vza_quartile"] = data["uc_id"].map(vza_group)
    data["longitude_quartile"] = data["uc_id"].map(lon_group)
    rows = []
    for grouping in ["vza_quartile", "longitude_quartile"]:
        for level, subset in data.groupby(grouping, observed=True):
            metrics = comparison_metrics(subset, cohort)
            metrics["stratifier"] = grouping
            metrics["stratum"] = int(level)
            rows.append(metrics)
    return pd.concat(rows, ignore_index=True)


def report_for(frame: pd.DataFrame, cohort: str) -> dict[str, object]:
    metrics = comparison_metrics(frame, cohort)
    indexed = metrics.set_index(["model", "scope", "component"])
    summary = {}
    for scope in ["hourly", "transition"]:
        for component in ["core", "ring", "anomaly"]:
            raw = indexed.loc[("raw", scope, component)]
            corrected = indexed.loc[("corrected", scope, component)]
            summary[f"{scope}_{component}"] = {
                "raw_rmse_k": float(raw["rmse_k"]),
                "corrected_rmse_k": float(corrected["rmse_k"]),
                "rmse_reduction_fraction": float(
                    1 - corrected["rmse_k"] / raw["rmse_k"]
                ),
                "raw_mean_bias_k": float(raw["mean_bias_k"]),
                "corrected_mean_bias_k": float(corrected["mean_bias_k"]),
            }
    transition_raw = indexed.loc[("raw", "transition", "anomaly")]
    transition_corrected = indexed.loc[("corrected", "transition", "anomaly")]
    summary["transition_anomaly"]["absolute_bias_reduction_fraction"] = float(
        1
        - abs(transition_corrected["mean_bias_k"])
        / abs(transition_raw["mean_bias_k"])
    )
    summary["transition_anomaly"]["raw_sign_disagreement"] = float(
        transition_raw["sign_disagreement"]
    )
    summary["transition_anomaly"]["corrected_sign_disagreement"] = float(
        transition_corrected["sign_disagreement"]
    )
    return {
        "cohort": cohort,
        "n_hourly": int(len(frame)),
        "n_cities": int(frame["uc_id"].nunique()),
        "n_intervals": int(frame["event_time_id"].nunique()),
        "n_transitions": int(len(transition_frame(frame))),
        "metrics": summary,
    }


def analyze(stage: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    model = joblib.load(MODEL_PATH)
    definition = DEFINITIONS[stage]
    frame = apply_models(aggregate_pair(definition), model)
    frame.to_parquet(OUT / f"{stage}_expanded_predictions.parquet", index=False)
    metrics = comparison_metrics(frame, f"expansion_{stage}")
    metrics.to_csv(OUT / f"{stage}_expanded_metrics.csv", index=False)
    stratified_metrics(frame, f"expansion_{stage}").to_csv(
        OUT / f"{stage}_expanded_stratified_metrics.csv", index=False
    )
    bootstrap = bootstrap_primary(frame)
    bootstrap.to_parquet(OUT / f"{stage}_expanded_bootstrap.parquet", index=False)
    bootstrap_summary = []
    for column in bootstrap.columns:
        if column == "iteration":
            continue
        bootstrap_summary.append(
            {
                "metric": column,
                "mean": bootstrap[column].mean(),
                "ci95_low": bootstrap[column].quantile(0.025),
                "ci95_high": bootstrap[column].quantile(0.975),
            }
        )
    pd.DataFrame(bootstrap_summary).to_csv(
        OUT / f"{stage}_expanded_bootstrap_summary.csv", index=False
    )
    leave_one_event_out(frame).to_csv(
        OUT / f"{stage}_expanded_leave_one_event_out.csv", index=False
    )
    report = report_for(frame, f"expansion_{stage}")
    (OUT / f"{stage}_expanded_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


def combine() -> None:
    original = pd.read_parquet(BASE_OUT / "validation_2025_predictions.parquet")
    expansion = pd.read_parquet(OUT / "validation_expanded_predictions.parquet")
    original["population_cohort"] = "original"
    expansion["population_cohort"] = "expansion"
    common = pd.concat([original, expansion], ignore_index=True)
    common.to_parquet(OUT / "combined_2025_common_domain_predictions.parquet", index=False)
    metrics = comparison_metrics(common, "combined_2025")
    metrics.to_csv(OUT / "combined_2025_metrics.csv", index=False)
    cohort_metrics = pd.concat(
        [
            comparison_metrics(group, cohort)
            for cohort, group in common.groupby("population_cohort", observed=True)
        ],
        ignore_index=True,
    )
    cohort_metrics.to_csv(OUT / "combined_2025_cohort_comparison.csv", index=False)
    report = report_for(common, "combined_2025")
    report["cohort_city_counts"] = {
        cohort: int(group["uc_id"].nunique())
        for cohort, group in common.groupby("population_cohort", observed=True)
    }
    (OUT / "combined_2025_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["historical", "validation", "combine"])
    args = parser.parse_args()
    if args.stage == "combine":
        combine()
    else:
        analyze(args.stage)


if __name__ == "__main__":
    main()
