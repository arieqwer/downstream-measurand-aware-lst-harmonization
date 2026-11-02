from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from run_multiplatform_harmonization import ccc, transition_frame, view_zenith_angle
from run_multiplatform_replication_audit import source_metadata
from train_goes18_goes19_metric_harmonization import (
    MODEL_PATH,
    predict_hourly,
    predict_transition,
)


ROOT = Path(__file__).resolve().parents[1]
DATA18 = ROOT / "data/goes18_2026_metric_holdout"
DATA19 = ROOT / "data/goes19_2026_metric_holdout"
OUT = ROOT / "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization"
PAIR_KEYS = [
    "uc_id",
    "event_year",
    "event_step8",
    "event_time_id",
    "local_date",
    "target_hour_from_sunset",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def raw_sensor(path: Path, sensor: str) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    frame["uc_id"] = frame["uc_id"].astype(str)
    frame["valid"] = (
        frame["core_recommended_count"].ge(3)
        & frame["ring_recommended_count"].ge(10)
        & frame["core_recommended_lst_k"].between(180, 380)
        & frame["ring_recommended_lst_k"].between(180, 380)
    )
    columns = [
        *PAIR_KEYS,
        "scan_time_utc",
        "source_key",
        "core_recommended_lst_k",
        "ring_recommended_lst_k",
        "valid",
    ]
    rename = {
        column: f"{column}_{sensor}" for column in columns if column not in PAIR_KEYS
    }
    return frame[columns].rename(columns=rename)


def projection(frame: pd.DataFrame, sensor: str, bucket: str) -> pd.DataFrame:
    key = f"source_key_{sensor}"
    representative = (
        frame[["event_time_id", key]]
        .dropna()
        .drop_duplicates()
        .sort_values(["event_time_id", key])
        .groupby("event_time_id", as_index=False)
        .first()
    )
    rows = []
    for row in representative.itertuples(index=False):
        metadata = source_metadata(bucket, getattr(row, key))
        rows.append({"event_time_id": row.event_time_id, **metadata})
    result = pd.DataFrame(rows)
    return result.rename(
        columns={
            "nominal_subpoint_lon": f"subpoint_lon_{sensor}",
            "nominal_subpoint_lat": f"subpoint_lat_{sensor}",
            "nominal_height_km": f"height_km_{sensor}",
        }
    )


def build_hourly_pair() -> pd.DataFrame:
    target = raw_sensor(DATA18 / "goes_sunset_hourly.parquet", "GOES18")
    source = raw_sensor(DATA19 / "goes_sunset_hourly.parquet", "GOES19")
    meta18 = projection(target, "GOES18", "noaa-goes18")
    meta19 = projection(source, "GOES19", "noaa-goes19")
    pair = target.merge(source, on=PAIR_KEYS, how="inner", validate="one_to_one")
    scan18 = pd.to_datetime(pair["scan_time_utc_GOES18"], utc=True, format="mixed")
    scan19 = pd.to_datetime(pair["scan_time_utc_GOES19"], utc=True, format="mixed")
    pair["scan_offset_min"] = (scan18 - scan19).dt.total_seconds().abs() / 60
    pair = pair[
        pair["valid_GOES18"].astype(bool)
        & pair["valid_GOES19"].astype(bool)
        & pair["scan_offset_min"].le(15)
    ].copy()
    keys = [
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "target_hour_from_sunset",
    ]
    hourly = pair.groupby(keys, observed=True).agg(
        n_paired_days=("local_date", "nunique"),
        target_core=("core_recommended_lst_k_GOES18", "mean"),
        target_ring=("ring_recommended_lst_k_GOES18", "mean"),
        source_core=("core_recommended_lst_k_GOES19", "mean"),
        source_ring=("ring_recommended_lst_k_GOES19", "mean"),
        scan_offset_min=("scan_offset_min", "mean"),
    ).reset_index()
    hourly["target_anomaly"] = hourly["target_core"] - hourly["target_ring"]
    hourly["source_anomaly"] = hourly["source_core"] - hourly["source_ring"]
    cities = pd.read_csv(DATA18 / "goes_sunset_cities.csv", dtype={"uc_id": str})
    hourly = hourly.merge(
        cities[["uc_id", "lat", "lon", "calibration_cohort"]],
        on="uc_id",
        how="left",
        validate="many_to_one",
    )
    hourly = hourly.merge(meta18, on="event_time_id", validate="many_to_one")
    hourly = hourly.merge(meta19, on="event_time_id", validate="many_to_one")
    hourly["vza_target"] = view_zenith_angle(
        hourly["lat"],
        hourly["lon"],
        hourly["subpoint_lat_GOES18"],
        hourly["subpoint_lon_GOES18"],
        hourly["height_km_GOES18"],
    )
    hourly["vza_source"] = view_zenith_angle(
        hourly["lat"],
        hourly["lon"],
        hourly["subpoint_lat_GOES19"],
        hourly["subpoint_lon_GOES19"],
        hourly["height_km_GOES19"],
    )
    hourly["vza_difference"] = hourly["vza_target"] - hourly["vza_source"]
    hourly["vza_mean"] = (hourly["vza_target"] + hourly["vza_source"]) / 2
    hourly["hydroclimatic_severity"] = np.nan
    hourly["t2m_true_night_pct_rank"] = np.nan
    hourly["true_night_heat"] = False
    return hourly


def apply_model(hourly: pd.DataFrame, model: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = hourly.copy()
    for component in ["core", "ring", "anomaly"]:
        result[f"metric_pred_{component}"] = predict_hourly(
            model["hourly"][component], result
        )
    result["pred_core"] = result["metric_pred_core"]
    result["pred_ring"] = result["metric_pred_ring"]
    result["component_derived_pred_anomaly"] = result["pred_core"] - result["pred_ring"]
    result["pred_anomaly"] = result["metric_pred_anomaly"]
    transitions = transition_frame(result)
    geometry = result[
        [
            "uc_id",
            "event_time_id",
            "lat",
            "lon",
            "vza_target",
            "vza_source",
            "vza_difference",
            "vza_mean",
            "calibration_cohort",
        ]
    ].drop_duplicates(["uc_id", "event_time_id"])
    transitions = transitions.merge(
        geometry,
        on=["uc_id", "event_time_id"],
        validate="one_to_one",
    )
    transitions["direct_transition_prediction"] = predict_transition(
        model["transition"], transitions
    )
    half_width = float(model["transition_uncertainty_half_width_k"])
    transitions["prediction_low"] = transitions["direct_transition_prediction"] - half_width
    transitions["prediction_high"] = transitions["direct_transition_prediction"] + half_width
    transitions["covered"] = (
        transitions["target_anomaly_transition"].ge(transitions["prediction_low"])
        & transitions["target_anomaly_transition"].le(transitions["prediction_high"])
    )
    transitions["certified_sign"] = np.select(
        [transitions["prediction_low"].gt(0), transitions["prediction_high"].lt(0)],
        [1, -1],
        default=0,
    )
    transitions["certified_correct"] = (
        transitions["certified_sign"]
        == np.sign(transitions["target_anomaly_transition"])
    )
    return result, transitions


def metric(target: pd.Series, estimate: pd.Series) -> dict[str, float]:
    target_array = target.to_numpy(dtype=float)
    estimate_array = estimate.to_numpy(dtype=float)
    error = estimate_array - target_array
    return {
        "mean_bias_k": float(error.mean()),
        "mae_k": float(np.abs(error).mean()),
        "rmse_k": float(np.sqrt(np.mean(error**2))),
        "ccc": ccc(target_array, estimate_array),
        "sign_disagreement": float(
            np.mean(np.sign(target_array) != np.sign(estimate_array))
        ),
        "n": int(len(error)),
    }


def metrics(hourly: pd.DataFrame, transitions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for component in ["core", "ring", "anomaly"]:
        for model_name, estimate in [
            ("raw", f"source_{component}"),
            ("metric_aware", f"metric_pred_{component}"),
        ]:
            rows.append(
                {
                    "scope": "hourly",
                    "component": component,
                    "model": model_name,
                    **metric(hourly[f"target_{component}"], hourly[estimate]),
                }
            )
    rows.append(
        {
            "scope": "hourly",
            "component": "anomaly",
            "model": "component_derived",
            **metric(
                hourly["target_anomaly"], hourly["component_derived_pred_anomaly"]
            ),
        }
    )
    transition_estimates = [
        ("raw", "source_anomaly_transition"),
        ("hourly_metric_derived", "pred_anomaly_transition"),
        ("direct_metric_aware", "direct_transition_prediction"),
    ]
    for model_name, estimate in transition_estimates:
        rows.append(
            {
                "scope": "transition",
                "component": "anomaly",
                "model": model_name,
                **metric(transitions["target_anomaly_transition"], transitions[estimate]),
            }
        )
    return pd.DataFrame(rows)


def uncertainty_summary(transitions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cohort, frame in [("combined", transitions), *transitions.groupby("calibration_cohort", observed=True)]:
        certified = frame[frame["certified_sign"].ne(0)]
        rows.append(
            {
                "cohort": cohort,
                "n": len(frame),
                "coverage": frame["covered"].mean(),
                "certified_fraction": len(certified) / len(frame),
                "certified_sign_accuracy": certified["certified_correct"].mean()
                if len(certified)
                else np.nan,
                "mean_interval_width_k": (
                    frame["prediction_high"] - frame["prediction_low"]
                ).mean(),
            }
        )
    for event, frame in transitions.groupby("event_time_id", observed=True):
        certified = frame[frame["certified_sign"].ne(0)]
        rows.append(
            {
                "cohort": f"event_{event}",
                "n": len(frame),
                "coverage": frame["covered"].mean(),
                "certified_fraction": len(certified) / len(frame),
                "certified_sign_accuracy": certified["certified_correct"].mean()
                if len(certified)
                else np.nan,
                "mean_interval_width_k": (
                    frame["prediction_high"] - frame["prediction_low"]
                ).mean(),
            }
        )
    return pd.DataFrame(rows)


def error_decomposition(hourly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model_name, core_name, ring_name in [
        ("raw", "source_core", "source_ring"),
        ("metric_aware_components", "metric_pred_core", "metric_pred_ring"),
    ]:
        core_error = hourly[core_name] - hourly["target_core"]
        ring_error = hourly[ring_name] - hourly["target_ring"]
        anomaly_error = core_error - ring_error
        covariance = np.cov(core_error, ring_error, ddof=0)[0, 1]
        rows.append(
            {
                "model": model_name,
                "core_error_variance": core_error.var(ddof=0),
                "ring_error_variance": ring_error.var(ddof=0),
                "core_ring_error_covariance": covariance,
                "core_ring_error_correlation": np.corrcoef(core_error, ring_error)[0, 1],
                "anomaly_error_variance_observed": anomaly_error.var(ddof=0),
                "anomaly_error_variance_identity": core_error.var(ddof=0)
                + ring_error.var(ddof=0)
                - 2 * covariance,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    model = joblib.load(MODEL_PATH)
    hourly = build_hourly_pair()
    predictions, transitions = apply_model(hourly, model)
    result_metrics = metrics(predictions, transitions)
    uncertainty = uncertainty_summary(transitions)
    decomposition = error_decomposition(predictions)
    predictions.to_parquet(OUT / "validation_2026_hourly_predictions.parquet", index=False)
    transitions.to_parquet(OUT / "validation_2026_transition_predictions.parquet", index=False)
    result_metrics.to_csv(OUT / "validation_2026_metrics.csv", index=False)
    uncertainty.to_csv(OUT / "validation_2026_uncertainty.csv", index=False)
    decomposition.to_csv(OUT / "validation_2026_error_decomposition.csv", index=False)

    indexed = result_metrics.set_index(["scope", "component", "model"])
    core_raw = indexed.loc[("hourly", "core", "raw"), "rmse_k"]
    core_cal = indexed.loc[("hourly", "core", "metric_aware"), "rmse_k"]
    ring_raw = indexed.loc[("hourly", "ring", "raw"), "rmse_k"]
    ring_cal = indexed.loc[("hourly", "ring", "metric_aware"), "rmse_k"]
    anomaly_raw = indexed.loc[("hourly", "anomaly", "raw"), "rmse_k"]
    anomaly_cal = indexed.loc[("hourly", "anomaly", "metric_aware"), "rmse_k"]
    transition_raw = indexed.loc[("transition", "anomaly", "raw"), "rmse_k"]
    transition_cal = indexed.loc[("transition", "anomaly", "direct_metric_aware"), "rmse_k"]
    combined_uncertainty = uncertainty[uncertainty["cohort"].eq("combined")].iloc[0]
    report = {
        "status": "frozen_2026_temporal_holdout_complete",
        "input_hashes": {
            "goes18": sha256(DATA18 / "goes_sunset_hourly.parquet"),
            "goes19": sha256(DATA19 / "goes_sunset_hourly.parquet"),
            "model": sha256(MODEL_PATH),
        },
        "n_hourly": int(len(predictions)),
        "n_transitions": int(len(transitions)),
        "n_cities": int(predictions["uc_id"].nunique()),
        "n_intervals": int(predictions["event_time_id"].nunique()),
        "rmse_reduction_fraction": {
            "core_hourly": float(1 - core_cal / core_raw),
            "ring_hourly": float(1 - ring_cal / ring_raw),
            "anomaly_hourly": float(1 - anomaly_cal / anomaly_raw),
            "anomaly_transition": float(1 - transition_cal / transition_raw),
        },
        "uncertainty_gate": combined_uncertainty.to_dict(),
        "prospective_criteria": {
            "core_and_ring_at_least_30pct": bool(
                1 - core_cal / core_raw >= 0.30 and 1 - ring_cal / ring_raw >= 0.30
            ),
            "hourly_anomaly_at_least_15pct": bool(1 - anomaly_cal / anomaly_raw >= 0.15),
            "transition_point_at_least_10pct": bool(
                1 - transition_cal / transition_raw >= 0.10
            ),
            "uncertainty_coverage_85_to_95pct": bool(
                0.85 <= combined_uncertainty["coverage"] <= 0.95
            ),
            "certified_sign_accuracy_at_least_90pct": bool(
                combined_uncertainty["certified_sign_accuracy"] >= 0.90
            ),
        },
    }
    (OUT / "validation_2026_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
