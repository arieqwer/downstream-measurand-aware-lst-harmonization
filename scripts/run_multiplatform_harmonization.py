from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

from run_goes_event_aware_inference import exact_wild_interval_test, fit_twfe
from run_multiplatform_replication_audit import (
    PAIR_DEFINITIONS,
    exact_hourly_pair,
    view_zenith_angle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/grl_deepening_2026/multiplatform_harmonization"
PROTOCOL = ROOT / "multiplatform_harmonization_protocol.md"
MODEL_PATH = OUT / "frozen_harmonization_model.joblib"
MANIFEST_PATH = OUT / "frozen_harmonization_manifest.json"
MODEL_ORDER = ["raw", "hour_offset", "hour_spline", "geometry_ridge"]
COMPONENTS = ["core", "ring", "anomaly"]
RIDGE_ALPHAS = np.logspace(-3, 4, 24)
SEED = 20260810


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def aggregate_pair(definition: dict[str, object]) -> pd.DataFrame:
    target = str(definition["sensor_a"])
    source = str(definition["sensor_b"])
    paired, metadata = exact_hourly_pair(definition)
    frame = paired[paired["paired_valid"]].copy()
    keys = [
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "target_hour_from_sunset",
    ]
    values = {
        "local_date": ("local_date", "nunique"),
        "target_core": (f"core_lst_k_{target}", "mean"),
        "target_ring": (f"ring_lst_k_{target}", "mean"),
        "source_core": (f"core_lst_k_{source}", "mean"),
        "source_ring": (f"ring_lst_k_{source}", "mean"),
        "scan_offset_min": ("scan_offset_min", "mean"),
        "hydroclimatic_severity": ("hydroclimatic_severity", "mean"),
        "t2m_true_night_pct_rank": ("t2m_true_night_pct_rank", "mean"),
        "true_night_heat": ("true_night_heat", "max"),
    }
    hourly = frame.groupby(keys, observed=True).agg(**values).reset_index()
    hourly = hourly.rename(columns={"local_date": "n_paired_days"})
    hourly["target_anomaly"] = hourly["target_core"] - hourly["target_ring"]
    hourly["source_anomaly"] = hourly["source_core"] - hourly["source_ring"]

    cities = pd.read_csv(Path(definition["cities"]), dtype={"uc_id": str})[
        ["uc_id", "lat", "lon"]
    ].drop_duplicates("uc_id")
    hourly = hourly.merge(cities, on="uc_id", how="left", validate="many_to_one")

    projection = metadata.pivot_table(
        index="event_time_id",
        columns="sensor",
        values=[
            "nominal_subpoint_lon",
            "nominal_subpoint_lat",
            "nominal_height_km",
        ],
        aggfunc="first",
    )
    projection.columns = [f"{name}_{sensor}" for name, sensor in projection.columns]
    projection = projection.reset_index()
    hourly = hourly.merge(
        projection, on="event_time_id", how="left", validate="many_to_one"
    )
    hourly["vza_target"] = view_zenith_angle(
        hourly["lat"],
        hourly["lon"],
        hourly[f"nominal_subpoint_lat_{target}"],
        hourly[f"nominal_subpoint_lon_{target}"],
        hourly[f"nominal_height_km_{target}"],
    )
    hourly["vza_source"] = view_zenith_angle(
        hourly["lat"],
        hourly["lon"],
        hourly[f"nominal_subpoint_lat_{source}"],
        hourly[f"nominal_subpoint_lon_{source}"],
        hourly[f"nominal_height_km_{source}"],
    )
    hourly["vza_difference"] = hourly["vza_target"] - hourly["vza_source"]
    hourly["vza_mean"] = (hourly["vza_target"] + hourly["vza_source"]) / 2
    hourly["period"] = str(definition["period"])
    hourly["target_sensor"] = target
    hourly["source_sensor"] = source
    needed = [
        "target_core",
        "target_ring",
        "source_core",
        "source_ring",
        "lat",
        "lon",
        "vza_target",
        "vza_source",
    ]
    return hourly.replace([np.inf, -np.inf], np.nan).dropna(subset=needed)


def assign_spatial_blocks(frame: pd.DataFrame) -> pd.DataFrame:
    cities = (
        frame[["uc_id", "lon"]]
        .drop_duplicates("uc_id")
        .sort_values(["lon", "uc_id"])
        .reset_index(drop=True)
    )
    cities["spatial_block"] = np.floor(
        np.arange(len(cities)) * 5 / len(cities)
    ).astype(int)
    return frame.merge(
        cities[["uc_id", "spatial_block"]],
        on="uc_id",
        how="left",
        validate="many_to_one",
    )


def geometry_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=frame.index)
    hour = frame["target_hour_from_sunset"].astype(float)
    result["hour"] = hour
    base = [
        "lat",
        "lon",
        "vza_target",
        "vza_source",
        "vza_difference",
        "vza_mean",
    ]
    for column in base:
        result[column] = frame[column].astype(float)
        result[f"hour_x_{column}"] = hour * frame[column].astype(float)
    return result


def fit_bias_model(frame: pd.DataFrame, model_name: str, component: str) -> dict:
    outcome = (
        frame[f"target_{component}"] - frame[f"source_{component}"]
    ).to_numpy(dtype=float)
    if model_name == "raw":
        return {"name": "raw", "component": component}
    if model_name == "hour_offset":
        offsets = (
            pd.DataFrame(
                {
                    "hour": frame["target_hour_from_sunset"].astype(int),
                    "bias": outcome,
                }
            )
            .groupby("hour", observed=True)["bias"]
            .mean()
            .to_dict()
        )
        return {"name": model_name, "component": component, "offsets": offsets}
    if model_name == "hour_spline":
        features = frame[["target_hour_from_sunset"]].to_numpy(dtype=float)
        pipeline = Pipeline(
            [
                (
                    "spline",
                    SplineTransformer(n_knots=5, degree=3, include_bias=True),
                ),
                ("ridge", RidgeCV(alphas=RIDGE_ALPHAS)),
            ]
        )
        pipeline.fit(features, outcome)
        return {"name": model_name, "component": component, "pipeline": pipeline}
    if model_name == "geometry_ridge":
        features = geometry_features(frame).to_numpy(dtype=float)
        pipeline = Pipeline(
            [
                ("scale", StandardScaler()),
                ("ridge", RidgeCV(alphas=RIDGE_ALPHAS)),
            ]
        )
        pipeline.fit(features, outcome)
        return {"name": model_name, "component": component, "pipeline": pipeline}
    raise ValueError(model_name)


def predict_bias(model: dict, frame: pd.DataFrame) -> np.ndarray:
    name = model["name"]
    if name == "raw":
        return np.zeros(len(frame))
    if name == "hour_offset":
        return (
            frame["target_hour_from_sunset"]
            .astype(int)
            .map(model["offsets"])
            .to_numpy(dtype=float)
        )
    if name == "hour_spline":
        features = frame[["target_hour_from_sunset"]].to_numpy(dtype=float)
        return model["pipeline"].predict(features)
    if name == "geometry_ridge":
        return model["pipeline"].predict(geometry_features(frame).to_numpy(dtype=float))
    raise ValueError(name)


def fit_models(frame: pd.DataFrame, model_name: str) -> dict:
    return {
        "name": model_name,
        "core": fit_bias_model(frame, model_name, "core"),
        "ring": fit_bias_model(frame, model_name, "ring"),
    }


def apply_models(frame: pd.DataFrame, model: dict) -> pd.DataFrame:
    result = frame.copy()
    result["pred_core"] = result["source_core"] + predict_bias(model["core"], result)
    result["pred_ring"] = result["source_ring"] + predict_bias(model["ring"], result)
    result["pred_anomaly"] = result["pred_core"] - result["pred_ring"]
    return result


def ccc(target: np.ndarray, estimate: np.ndarray) -> float:
    target = np.asarray(target, dtype=float)
    estimate = np.asarray(estimate, dtype=float)
    covariance = np.mean((target - target.mean()) * (estimate - estimate.mean()))
    denominator = (
        target.var(ddof=0)
        + estimate.var(ddof=0)
        + (target.mean() - estimate.mean()) ** 2
    )
    return float(2 * covariance / denominator) if denominator > 0 else np.nan


def transition_frame(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["window"] = np.select(
        [
            data["target_hour_from_sunset"].between(-3, -1),
            data["target_hour_from_sunset"].between(4, 6),
        ],
        ["pre", "late"],
        default="other",
    )
    data = data[data["window"].isin(["pre", "late"])]
    data["target_surface"] = (data["target_core"] + data["target_ring"]) / 2
    data["source_surface"] = (data["source_core"] + data["source_ring"]) / 2
    data["pred_surface"] = (data["pred_core"] + data["pred_ring"]) / 2
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
        "target_surface",
        "source_surface",
        "pred_surface",
    ]
    grouped = data.groupby(keys, observed=True).agg(
        **{column: (column, "mean") for column in measures},
        n_hours=("target_hour_from_sunset", "nunique"),
        hydroclimatic_severity=("hydroclimatic_severity", "mean"),
        t2m_true_night_pct_rank=("t2m_true_night_pct_rank", "mean"),
        true_night_heat=("true_night_heat", "max"),
        scan_offset_min=("scan_offset_min", "mean"),
    ).reset_index()
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
    for column in [
        "hydroclimatic_severity",
        "t2m_true_night_pct_rank",
        "scan_offset_min",
    ]:
        wide[column] = wide[[f"{column}_pre", f"{column}_late"]].mean(axis=1)
    wide["true_night_heat"] = wide[
        ["true_night_heat_pre", "true_night_heat_late"]
    ].max(axis=1).astype(bool)
    return wide.dropna(
        subset=[
            "target_anomaly_transition",
            "source_anomaly_transition",
            "pred_anomaly_transition",
        ]
    )


def metric_rows(frame: pd.DataFrame, estimate_prefix: str, label: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for component in COMPONENTS:
        target = frame[f"target_{component}"].to_numpy(dtype=float)
        estimate = frame[f"{estimate_prefix}_{component}"].to_numpy(dtype=float)
        error = estimate - target
        rows.append(
            {
                "model": label,
                "scope": "hourly",
                "component": component,
                "mean_bias_k": error.mean(),
                "mae_k": np.abs(error).mean(),
                "rmse_k": np.sqrt(np.mean(error**2)),
                "ccc": ccc(target, estimate),
                "n": len(error),
            }
        )
    transitions = transition_frame(frame)
    for component in COMPONENTS:
        target = transitions[f"target_{component}_transition"].to_numpy(dtype=float)
        estimate = transitions[f"{estimate_prefix}_{component}_transition"].to_numpy(dtype=float)
        error = estimate - target
        rows.append(
            {
                "model": label,
                "scope": "transition",
                "component": component,
                "mean_bias_k": error.mean(),
                "mae_k": np.abs(error).mean(),
                "rmse_k": np.sqrt(np.mean(error**2)),
                "ccc": ccc(target, estimate),
                "n": len(error),
                "sign_disagreement": np.mean(np.sign(target) != np.sign(estimate)),
            }
        )
    return pd.DataFrame(rows)


def cross_validate(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    data = assign_spatial_blocks(frame)
    prediction_frames = []
    fold_metrics = []
    years = sorted(data["event_year"].unique())
    blocks = sorted(data["spatial_block"].unique())
    for year in years:
        for block in blocks:
            test_mask = data["event_year"].eq(year) & data["spatial_block"].eq(block)
            train_mask = data["event_year"].ne(year) & data["spatial_block"].ne(block)
            train = data[train_mask].copy()
            test = data[test_mask].copy()
            if train.empty or test.empty:
                continue
            fold = f"year_{year}_block_{block}"
            raw = test.copy()
            raw["pred_core"] = raw["source_core"]
            raw["pred_ring"] = raw["source_ring"]
            raw["pred_anomaly"] = raw["source_anomaly"]
            raw_metrics = metric_rows(raw, "pred", "raw")
            raw_rmse = {
                (row.scope, row.component): row.rmse_k
                for row in raw_metrics.itertuples(index=False)
            }
            for model_name in MODEL_ORDER:
                models = fit_models(train, model_name)
                predicted = apply_models(test, models)
                predicted["candidate_model"] = model_name
                predicted["cv_fold"] = fold
                prediction_frames.append(predicted)
                metrics = metric_rows(predicted, "pred", model_name)
                metrics["cv_fold"] = fold
                metrics["rmse_ratio_to_raw"] = [
                    row.rmse_k / raw_rmse[(row.scope, row.component)]
                    for row in metrics.itertuples(index=False)
                ]
                fold_metrics.append(metrics)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    metrics = pd.concat(fold_metrics, ignore_index=True)
    fold_scores = (
        metrics.groupby(["model", "cv_fold"], observed=True)["rmse_ratio_to_raw"]
        .mean()
        .rename("composite_rmse_ratio")
        .reset_index()
    )
    summary = fold_scores.groupby("model", observed=True).agg(
        mean_composite=("composite_rmse_ratio", "mean"),
        sd_composite=("composite_rmse_ratio", "std"),
        n_folds=("composite_rmse_ratio", "size"),
    ).reset_index()
    summary["se_composite"] = summary["sd_composite"] / np.sqrt(summary["n_folds"])
    best = summary.loc[summary["mean_composite"].idxmin()]
    threshold = float(best["mean_composite"] + best["se_composite"])
    eligible = set(summary.loc[summary["mean_composite"].le(threshold), "model"])
    selected = next(model for model in MODEL_ORDER if model in eligible)
    summary["one_se_threshold"] = threshold
    summary["selected"] = summary["model"].eq(selected)
    metrics = metrics.merge(fold_scores, on=["model", "cv_fold"], how="left")
    return predictions, metrics.merge(summary, on="model", how="left"), selected


def derive() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    derivation = aggregate_pair(PAIR_DEFINITIONS[0])
    derivation.to_parquet(OUT / "derivation_city_event_hourly.parquet", index=False)
    predictions, cv_metrics, selected = cross_validate(derivation)
    predictions.to_parquet(OUT / "derivation_cross_validated_predictions.parquet", index=False)
    cv_metrics.to_csv(OUT / "derivation_cross_validation_metrics.csv", index=False)
    selection = (
        cv_metrics[
            [
                "model",
                "mean_composite",
                "sd_composite",
                "se_composite",
                "n_folds",
                "one_se_threshold",
                "selected",
            ]
        ]
        .drop_duplicates("model")
        .sort_values("mean_composite")
    )
    selection.to_csv(OUT / "derivation_model_selection.csv", index=False)
    final_model = fit_models(derivation, selected)
    joblib.dump(final_model, MODEL_PATH)
    manifest = {
        "stage": "derivation_complete_validation_not_opened_by_this_stage",
        "protocol": str(PROTOCOL),
        "protocol_sha256": sha256(PROTOCOL),
        "selected_model": selected,
        "n_hourly": int(len(derivation)),
        "n_cities": int(derivation["uc_id"].nunique()),
        "n_intervals": int(derivation["event_time_id"].nunique()),
        "years": sorted(map(int, derivation["event_year"].unique())),
        "model_sha256": sha256(MODEL_PATH),
        "selection": selection.to_dict(orient="records"),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def weighted_rmse(error: np.ndarray, weight: np.ndarray) -> float:
    return float(np.sqrt(np.average(error**2, weights=weight)))


def weighted_mean(value: np.ndarray, weight: np.ndarray) -> float:
    return float(np.average(value, weights=weight))


def bootstrap_primary(frame: pd.DataFrame, n_boot: int = 5000) -> pd.DataFrame:
    transitions = transition_frame(frame)
    cities = np.array(sorted(frame["uc_id"].unique()))
    events = np.array(sorted(frame["event_time_id"].unique()))
    rng = np.random.default_rng(SEED)
    rows = []
    hourly_raw_error = frame["source_anomaly"].to_numpy() - frame["target_anomaly"].to_numpy()
    hourly_cor_error = frame["pred_anomaly"].to_numpy() - frame["target_anomaly"].to_numpy()
    transition_raw_error = (
        transitions["source_anomaly_transition"]
        - transitions["target_anomaly_transition"]
    ).to_numpy()
    transition_cor_error = (
        transitions["pred_anomaly_transition"]
        - transitions["target_anomaly_transition"]
    ).to_numpy()
    for iteration in range(n_boot):
        city_counts = pd.Series(rng.choice(cities, len(cities), replace=True)).value_counts()
        event_counts = pd.Series(rng.choice(events, len(events), replace=True)).value_counts()
        hourly_weight = (
            frame["uc_id"].map(city_counts).fillna(0).to_numpy()
            * frame["event_time_id"].map(event_counts).fillna(0).to_numpy()
        )
        transition_weight = (
            transitions["uc_id"].map(city_counts).fillna(0).to_numpy()
            * transitions["event_time_id"].map(event_counts).fillna(0).to_numpy()
        )
        if hourly_weight.sum() == 0 or transition_weight.sum() == 0:
            continue
        h_raw = weighted_rmse(hourly_raw_error, hourly_weight)
        h_cor = weighted_rmse(hourly_cor_error, hourly_weight)
        t_raw = weighted_rmse(transition_raw_error, transition_weight)
        t_cor = weighted_rmse(transition_cor_error, transition_weight)
        target_transition = transitions["target_anomaly_transition"].to_numpy()
        raw_transition = transitions["source_anomaly_transition"].to_numpy()
        cor_transition = transitions["pred_anomaly_transition"].to_numpy()
        raw_sign = weighted_mean(
            (np.sign(target_transition) != np.sign(raw_transition)).astype(float),
            transition_weight,
        )
        cor_sign = weighted_mean(
            (np.sign(target_transition) != np.sign(cor_transition)).astype(float),
            transition_weight,
        )
        rows.append(
            {
                "iteration": iteration,
                "hourly_rmse_reduction_fraction": 1 - h_cor / h_raw,
                "transition_rmse_reduction_fraction": 1 - t_cor / t_raw,
                "raw_transition_mean_bias_k": weighted_mean(
                    transition_raw_error, transition_weight
                ),
                "corrected_transition_mean_bias_k": weighted_mean(
                    transition_cor_error, transition_weight
                ),
                "sign_disagreement_change": cor_sign - raw_sign,
            }
        )
    return pd.DataFrame(rows)


def leave_one_event_out(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event in sorted(frame["event_time_id"].unique()):
        subset = frame[frame["event_time_id"].ne(event)].copy()
        metrics = pd.concat(
            [
                metric_rows(subset, "source", "raw"),
                metric_rows(subset, "pred", "corrected"),
            ],
            ignore_index=True,
        )
        for scope in ["hourly", "transition"]:
            selected = metrics[
                metrics["scope"].eq(scope) & metrics["component"].eq("anomaly")
            ].set_index("model")
            rows.append(
                {
                    "omitted_event_time_id": event,
                    "scope": scope,
                    "raw_rmse_k": selected.loc["raw", "rmse_k"],
                    "corrected_rmse_k": selected.loc["corrected", "rmse_k"],
                    "rmse_reduction_fraction": 1
                    - selected.loc["corrected", "rmse_k"]
                    / selected.loc["raw", "rmse_k"],
                }
            )
    return pd.DataFrame(rows)


def temporal_artifact_analysis(
    historical: pd.DataFrame, validation: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    panels = []
    for frame, is_2025 in [(historical, 0.0), (validation, 1.0)]:
        event = transition_frame(frame)
        event = event[event["true_night_heat"]].copy()
        event["period_2025"] = is_2025
        event["severity10"] = event["hydroclimatic_severity"] / 10
        event["severity_x_2025"] = event["severity10"] * is_2025
        event["transition_consensus_raw"] = (
            event["target_anomaly_transition"]
            + event["source_anomaly_transition"]
        ) / 2
        event["transition_consensus_corrected"] = (
            event["target_anomaly_transition"]
            + event["pred_anomaly_transition"]
        ) / 2
        event["pre_surface_consensus_raw"] = (
            event["target_surface_pre"] + event["source_surface_pre"]
        ) / 2
        event["pre_surface_consensus_corrected"] = (
            event["target_surface_pre"] + event["pred_surface_pre"]
        ) / 2
        panels.append(event)
    panel = pd.concat(panels, ignore_index=True)
    model_rows = []
    wild_rows = []
    for version in ["raw", "corrected"]:
        data = panel.copy()
        for column in [
            "t2m_true_night_pct_rank",
            f"pre_surface_consensus_{version}",
            "scan_offset_min",
        ]:
            data[f"z_{column}"] = (data[column] - data[column].mean()) / data[column].std(ddof=0)
        predictors = [
            "severity10",
            "severity_x_2025",
            "z_t2m_true_night_pct_rank",
            f"z_pre_surface_consensus_{version}",
            "z_scan_offset_min",
        ]
        outcome = f"transition_consensus_{version}"
        model, _ = fit_twfe(data, outcome, predictors, f"temporal_transfer_{version}")
        wild = exact_wild_interval_test(
            data, outcome, predictors, "severity_x_2025"
        )
        wild.update(
            {
                "analysis": f"temporal_transfer_{version}",
                "outcome": outcome,
                "focal_term": "severity_x_2025",
            }
        )
        model_rows.append(model)
        wild_rows.append(wild)
    return pd.concat(model_rows, ignore_index=True), pd.DataFrame(wild_rows)


def validate() -> None:
    if not MODEL_PATH.exists() or not MANIFEST_PATH.exists():
        raise FileNotFoundError("Run --stage derive before opening validation data")
    model = joblib.load(MODEL_PATH)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["model_sha256"] != sha256(MODEL_PATH):
        raise RuntimeError("Frozen model hash mismatch")
    validation = aggregate_pair(PAIR_DEFINITIONS[1])
    corrected = apply_models(validation, model)
    corrected.to_parquet(OUT / "validation_2025_predictions.parquet", index=False)
    metrics = pd.concat(
        [
            metric_rows(corrected, "source", "raw"),
            metric_rows(corrected, "pred", "corrected"),
        ],
        ignore_index=True,
    )
    metrics.to_csv(OUT / "validation_2025_metrics.csv", index=False)

    indexed = metrics.set_index(["model", "scope", "component"])
    h_raw = indexed.loc[("raw", "hourly", "anomaly"), "rmse_k"]
    h_cor = indexed.loc[("corrected", "hourly", "anomaly"), "rmse_k"]
    t_raw = indexed.loc[("raw", "transition", "anomaly"), "rmse_k"]
    t_cor = indexed.loc[("corrected", "transition", "anomaly"), "rmse_k"]
    b_raw = abs(indexed.loc[("raw", "transition", "anomaly"), "mean_bias_k"])
    b_cor = abs(indexed.loc[("corrected", "transition", "anomaly"), "mean_bias_k"])
    s_raw = indexed.loc[("raw", "transition", "anomaly"), "sign_disagreement"]
    s_cor = indexed.loc[("corrected", "transition", "anomaly"), "sign_disagreement"]
    success = {
        "hourly_anomaly_rmse_reduction_fraction": 1 - h_cor / h_raw,
        "transition_anomaly_rmse_reduction_fraction": 1 - t_cor / t_raw,
        "transition_absolute_bias_reduction_fraction": 1 - b_cor / b_raw,
        "transition_sign_disagreement_change": s_cor - s_raw,
    }
    success["all_primary_criteria_met"] = bool(
        success["hourly_anomaly_rmse_reduction_fraction"] >= 0.10
        and success["transition_anomaly_rmse_reduction_fraction"] >= 0.10
        and success["transition_absolute_bias_reduction_fraction"] >= 0.50
        and success["transition_sign_disagreement_change"] <= 0.05
    )

    bootstrap = bootstrap_primary(corrected)
    bootstrap.to_parquet(OUT / "validation_crossed_bootstrap.parquet", index=False)
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
        OUT / "validation_crossed_bootstrap_summary.csv", index=False
    )
    loo = leave_one_event_out(corrected)
    loo.to_csv(OUT / "validation_leave_one_event_out.csv", index=False)
    strong = bool(
        success["hourly_anomaly_rmse_reduction_fraction"] >= 0.20
        and success["transition_anomaly_rmse_reduction_fraction"] >= 0.20
        and loo["rmse_reduction_fraction"].gt(0).all()
    )

    historical = pd.read_parquet(OUT / "derivation_city_event_hourly.parquet")
    historical = apply_models(historical, model)
    temporal_models, temporal_wild = temporal_artifact_analysis(historical, corrected)
    temporal_models.to_csv(OUT / "temporal_artifact_models.csv", index=False)
    temporal_wild.to_csv(OUT / "temporal_artifact_wild_tests.csv", index=False)

    report = {
        "status": "independent_2025_validation_complete",
        "selected_model": model["name"],
        "n_hourly": int(len(corrected)),
        "n_cities": int(corrected["uc_id"].nunique()),
        "n_intervals": int(corrected["event_time_id"].nunique()),
        "success_metrics": success,
        "strong_transfer_criteria_met": strong,
        "leave_one_event_out_min_rmse_reduction": float(
            loo["rmse_reduction_fraction"].min()
        ),
        "leave_one_event_out_max_rmse_reduction": float(
            loo["rmse_reduction_fraction"].max()
        ),
        "temporal_wild_tests": temporal_wild.to_dict(orient="records"),
    }
    (OUT / "validation_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["derive", "validate"], required=True)
    args = parser.parse_args()
    if args.stage == "derive":
        derive()
    else:
        validate()


if __name__ == "__main__":
    main()
