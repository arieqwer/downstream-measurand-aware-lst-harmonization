from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_downstream_metric_framework import mse_budget


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "GOES17_GOES16_EXTERNAL_METRIC_REPLICATION_PROTOCOL.md"
DATA16 = ROOT / "data/goes16_2019_2021_external_metric"
DATA17 = ROOT / "data/goes17_2019_2021_external_metric"
OUT = ROOT / "outputs/grl_deepening_2026/goes17_goes16_external_metric"
SEED = 20260810
BOOTSTRAP_DRAWS = 5000
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
    frame = pd.read_parquet(path).copy()
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
        "core_recommended_lst_k",
        "ring_recommended_lst_k",
        "valid",
    ]
    rename = {
        column: f"{column}_{sensor}" for column in columns if column not in PAIR_KEYS
    }
    return frame[columns].rename(columns=rename)


def build_hourly_pair() -> tuple[pd.DataFrame, pd.DataFrame]:
    target = raw_sensor(DATA17 / "goes_sunset_hourly.parquet", "GOES17")
    source = raw_sensor(DATA16 / "goes_sunset_hourly.parquet", "GOES16")
    pair = target.merge(source, on=PAIR_KEYS, how="inner", validate="one_to_one")
    scan17 = pd.to_datetime(pair["scan_time_utc_GOES17"], utc=True, format="mixed")
    scan16 = pd.to_datetime(pair["scan_time_utc_GOES16"], utc=True, format="mixed")
    pair["scan_offset_min"] = (scan17 - scan16).dt.total_seconds().abs() / 60
    pair["paired_valid"] = (
        pair["valid_GOES17"].astype(bool)
        & pair["valid_GOES16"].astype(bool)
        & pair["scan_offset_min"].le(15)
    )

    keys = [
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "target_hour_from_sunset",
    ]
    hourly = (
        pair[pair["paired_valid"]]
        .groupby(keys, observed=True)
        .agg(
            n_paired_days=("local_date", "nunique"),
            target_core=("core_recommended_lst_k_GOES17", "mean"),
            target_ring=("ring_recommended_lst_k_GOES17", "mean"),
            source_core=("core_recommended_lst_k_GOES16", "mean"),
            source_ring=("ring_recommended_lst_k_GOES16", "mean"),
            scan_offset_min=("scan_offset_min", "mean"),
        )
        .reset_index()
    )
    hourly = hourly[hourly["n_paired_days"].ge(2)].copy()
    hourly["target_anomaly"] = hourly["target_core"] - hourly["target_ring"]
    hourly["source_anomaly"] = hourly["source_core"] - hourly["source_ring"]
    hourly["analysis_role"] = np.where(
        hourly["event_year"].le(2020), "calibration", "validation"
    )

    attrition = []
    for event_id in sorted(pair["event_time_id"].unique()):
        source_event = pair[pair["event_time_id"].eq(event_id)]
        valid_event = source_event[source_event["paired_valid"]]
        aggregated_event = hourly[hourly["event_time_id"].eq(event_id)]
        attrition.append(
            {
                "event_time_id": int(event_id),
                "event_year": int(source_event["event_year"].iloc[0]),
                "analysis_role": (
                    "calibration"
                    if int(source_event["event_year"].iloc[0]) <= 2020
                    else "validation"
                ),
                "candidate_daily_rows": int(len(source_event)),
                "paired_valid_daily_rows": int(len(valid_event)),
                "retained_city_event_hour_rows": int(len(aggregated_event)),
                "retained_cities": int(aggregated_event["uc_id"].nunique()),
                "retained_hours": int(
                    aggregated_event["target_hour_from_sunset"].nunique()
                ),
            }
        )
    return hourly, pd.DataFrame(attrition)


def fit_hour_offsets(calibration: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for hour, frame in calibration.groupby("target_hour_from_sunset", observed=True):
        rows.append(
            {
                "target_hour_from_sunset": int(hour),
                "core_offset_k": float((frame["target_core"] - frame["source_core"]).mean()),
                "ring_offset_k": float((frame["target_ring"] - frame["source_ring"]).mean()),
                "n_calibration_rows": int(len(frame)),
                "n_calibration_cities": int(frame["uc_id"].nunique()),
                "n_calibration_events": int(frame["event_time_id"].nunique()),
            }
        )
    result = pd.DataFrame(rows).sort_values("target_hour_from_sunset")
    expected = set(range(-3, 7))
    observed = set(result["target_hour_from_sunset"])
    if observed != expected:
        raise AssertionError(f"Frozen hours missing from calibration: {sorted(expected-observed)}")
    return result


def apply_offsets(hourly: pd.DataFrame, offsets: pd.DataFrame) -> pd.DataFrame:
    result = hourly.merge(
        offsets[
            ["target_hour_from_sunset", "core_offset_k", "ring_offset_k"]
        ],
        on="target_hour_from_sunset",
        how="left",
        validate="many_to_one",
    )
    result["pred_core"] = result["source_core"] + result["core_offset_k"]
    result["pred_ring"] = result["source_ring"] + result["ring_offset_k"]
    result["pred_anomaly"] = result["pred_core"] - result["pred_ring"]
    return result


def transition_frame(hourly: pd.DataFrame) -> pd.DataFrame:
    frame = hourly.copy()
    frame["window"] = np.select(
        [
            frame["target_hour_from_sunset"].between(-3, -1),
            frame["target_hour_from_sunset"].between(4, 6),
        ],
        ["pre", "late"],
        default="other",
    )
    frame = frame[frame["window"].isin(["pre", "late"])]
    keys = ["uc_id", "event_year", "event_step8", "event_time_id", "window"]
    measures = [
        "target_core",
        "target_ring",
        "target_anomaly",
        "source_core",
        "source_ring",
        "source_anomaly",
        "pred_core",
        "pred_ring",
        "pred_anomaly",
    ]
    grouped = (
        frame.groupby(keys, observed=True)
        .agg(
            **{column: (column, "mean") for column in measures},
            n_hours=("target_hour_from_sunset", "nunique"),
            scan_offset_min=("scan_offset_min", "mean"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["n_hours"].ge(2)]
    index = ["uc_id", "event_year", "event_step8", "event_time_id"]
    wide = grouped.pivot(index=index, columns="window")
    wide.columns = [f"{name}_{window}" for name, window in wide.columns]
    wide = wide.reset_index()
    for prefix in ["target", "source", "pred"]:
        for component in ["core", "ring", "anomaly"]:
            wide[f"{prefix}_{component}_transition"] = (
                wide[f"{prefix}_{component}_late"]
                - wide[f"{prefix}_{component}_pre"]
            )
    return wide.dropna(
        subset=[
            "target_anomaly_transition",
            "source_anomaly_transition",
            "pred_anomaly_transition",
        ]
    )


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.average(values, weights=weights))


def weighted_rmse(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sqrt(np.average(values**2, weights=weights)))


def performance(
    frame: pd.DataFrame, scope: str, weights: np.ndarray | None = None
) -> dict[str, float]:
    suffix = "" if scope == "hourly" else "_transition"
    if weights is None:
        weights = np.ones(len(frame), dtype=float)
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
    raw_anomaly = raw_core - raw_ring
    harm_anomaly = harm_core - harm_ring
    raw_core_rmse = weighted_rmse(raw_core, weights)
    raw_ring_rmse = weighted_rmse(raw_ring, weights)
    raw_anomaly_rmse = weighted_rmse(raw_anomaly, weights)
    harm_core_rmse = weighted_rmse(harm_core, weights)
    harm_ring_rmse = weighted_rmse(harm_ring, weights)
    harm_anomaly_rmse = weighted_rmse(harm_anomaly, weights)
    return {
        "raw_core_rmse_k": raw_core_rmse,
        "harm_core_rmse_k": harm_core_rmse,
        "core_rmse_reduction_fraction": 1 - harm_core_rmse / raw_core_rmse,
        "raw_ring_rmse_k": raw_ring_rmse,
        "harm_ring_rmse_k": harm_ring_rmse,
        "ring_rmse_reduction_fraction": 1 - harm_ring_rmse / raw_ring_rmse,
        "raw_anomaly_rmse_k": raw_anomaly_rmse,
        "harm_anomaly_rmse_k": harm_anomaly_rmse,
        "anomaly_rmse_reduction_fraction": 1
        - harm_anomaly_rmse / raw_anomaly_rmse,
        "raw_error_correlation": float(np.corrcoef(raw_core, raw_ring)[0, 1]),
        "harm_error_correlation": float(np.corrcoef(harm_core, harm_ring)[0, 1]),
        "mean_raw_anomaly_error_k": weighted_mean(raw_anomaly, weights),
        "mean_harm_anomaly_error_k": weighted_mean(harm_anomaly, weights),
    }


def crossed_bootstrap(
    hourly: pd.DataFrame,
    transitions: pd.DataFrame,
    draws: int = BOOTSTRAP_DRAWS,
) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    cities = np.array(sorted(hourly["uc_id"].unique()))
    events = np.array(sorted(hourly["event_time_id"].unique()))
    rows = []
    for iteration in range(draws):
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
                    "scope": scope,
                    **performance(frame, scope, weights),
                    **mse_budget(frame, scope, weights),
                }
            )
    return pd.DataFrame(rows)


def summarize_bootstrap(bootstrap: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "core_rmse_reduction_fraction",
        "ring_rmse_reduction_fraction",
        "anomaly_rmse_reduction_fraction",
        "component_variance_gain_k2",
        "differential_bias_gain_k2",
        "covariance_loss_penalty_k2",
        "net_downstream_mse_gain_k2",
        "net_downstream_mse_gain_fraction",
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


def influence_diagnostics(hourly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event_id, frame in hourly.groupby("event_time_id", observed=True):
        rows.append(
            {
                "diagnostic": "single_event",
                "event_time_id": int(event_id),
                "n": int(len(frame)),
                "n_cities": int(frame["uc_id"].nunique()),
                **performance(frame, "hourly"),
                **mse_budget(frame, "hourly"),
            }
        )
    for event_id in sorted(hourly["event_time_id"].unique()):
        frame = hourly[hourly["event_time_id"].ne(event_id)]
        rows.append(
            {
                "diagnostic": "leave_one_event_out",
                "event_time_id": int(event_id),
                "n": int(len(frame)),
                "n_cities": int(frame["uc_id"].nunique()),
                **performance(frame, "hourly"),
                **mse_budget(frame, "hourly"),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hourly, attrition = build_hourly_pair()
    calibration = hourly[hourly["analysis_role"].eq("calibration")].copy()
    validation = hourly[hourly["analysis_role"].eq("validation")].copy()
    offsets = fit_hour_offsets(calibration)
    validation = apply_offsets(validation, offsets)
    transitions = transition_frame(validation)

    point_rows = []
    for scope, frame in [("hourly", validation), ("transition", transitions)]:
        point_rows.append(
            {
                "scope": scope,
                "n_cities": int(frame["uc_id"].nunique()),
                "n_events": int(frame["event_time_id"].nunique()),
                "n": int(len(frame)),
                **performance(frame, scope),
                **mse_budget(frame, scope),
            }
        )
    points = pd.DataFrame(point_rows)
    bootstrap = crossed_bootstrap(validation, transitions)
    summary = summarize_bootstrap(bootstrap)
    influence = influence_diagnostics(validation)

    attrition.to_csv(OUT / "event_attrition.csv", index=False)
    offsets.to_csv(OUT / "frozen_hour_offsets_2019_2020.csv", index=False)
    validation.to_parquet(OUT / "validation_2021_hourly_predictions.parquet", index=False)
    transitions.to_parquet(OUT / "validation_2021_transition_predictions.parquet", index=False)
    points.to_csv(OUT / "validation_2021_exact_mse_budget.csv", index=False)
    bootstrap.to_parquet(OUT / "validation_2021_crossed_bootstrap.parquet", index=False)
    summary.to_csv(OUT / "validation_2021_bootstrap_summary.csv", index=False)
    influence.to_csv(OUT / "validation_2021_event_influence.csv", index=False)

    hourly_point = points[points["scope"].eq("hourly")].iloc[0]
    report = {
        "status": "frozen_external_replication_complete",
        "target_sensor": "GOES17",
        "source_sensor": "GOES16",
        "input_hashes": {
            "protocol": sha256(PROTOCOL),
            "goes16": sha256(DATA16 / "goes_sunset_hourly.parquet"),
            "goes17": sha256(DATA17 / "goes_sunset_hourly.parquet"),
            "goes16_manifest": sha256(DATA16 / "FROZEN_SELECTION.json"),
            "goes17_manifest": sha256(DATA17 / "FROZEN_SELECTION.json"),
        },
        "calibration": {
            "years": [2019, 2020],
            "n_rows": int(len(calibration)),
            "n_cities": int(calibration["uc_id"].nunique()),
            "n_events": int(calibration["event_time_id"].nunique()),
        },
        "validation": {
            "year": 2021,
            "n_hourly": int(len(validation)),
            "n_transitions": int(len(transitions)),
            "n_cities": int(validation["uc_id"].nunique()),
            "n_events": int(validation["event_time_id"].nunique()),
        },
        "primary_external_criteria": {
            "core_rmse_improves": bool(
                hourly_point["core_rmse_reduction_fraction"] > 0
            ),
            "ring_rmse_improves": bool(
                hourly_point["ring_rmse_reduction_fraction"] > 0
            ),
            "core_ring_error_covariance_declines": bool(
                hourly_point["covariance_loss_penalty_k2"] > 0
            ),
            "downstream_gain_attenuated_by_covariance_loss": bool(
                hourly_point["covariance_loss_penalty_k2"] > 0
                and hourly_point["net_downstream_mse_gain_k2"]
                < hourly_point["component_variance_gain_k2"]
                + hourly_point["differential_bias_gain_k2"]
            ),
        },
        "post_analysis_influence_diagnostics": {
            "purpose": "descriptive influence audit only; no model selection or tuning",
            "all_four_single_events_core_and_ring_improve": bool(
                (
                    influence[influence["diagnostic"].eq("single_event")][
                        [
                            "core_rmse_reduction_fraction",
                            "ring_rmse_reduction_fraction",
                        ]
                    ]
                    > 0
                )
                .all()
                .all()
            ),
            "all_four_single_events_covariance_penalty_positive": bool(
                (
                    influence[influence["diagnostic"].eq("single_event")][
                        "covariance_loss_penalty_k2"
                    ]
                    > 0
                ).all()
            ),
        },
        "point_estimates": points.to_dict(orient="records"),
    }
    (OUT / "external_replication_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
