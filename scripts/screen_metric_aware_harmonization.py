from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from run_multiplatform_harmonization import (
    OUT as BASE_OUT,
    RIDGE_ALPHAS,
    assign_spatial_blocks,
    ccc,
    transition_frame,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/grl_deepening_2026/metric_aware_harmonization_screen"
HOURLY_MODELS = ["raw", "hour_offset", "geometry_ridge", "scene_ridge", "scene_gbdt"]
TRANSITION_MODELS = ["raw", "mean_offset", "transition_ridge", "transition_gbdt"]


def hourly_features(frame: pd.DataFrame, mode: str) -> pd.DataFrame:
    hour = pd.get_dummies(
        frame["target_hour_from_sunset"].astype(int), prefix="hour", dtype=float
    ).reindex(columns=[f"hour_{h}" for h in range(-3, 7)], fill_value=0.0)
    geometry = frame[
        ["lat", "lon", "vza_target", "vza_source", "vza_difference", "vza_mean"]
    ].astype(float).reset_index(drop=True)
    if mode == "geometry_ridge":
        return pd.concat([hour.reset_index(drop=True), geometry], axis=1)
    scene = pd.DataFrame(
        {
            "source_core": frame["source_core"].to_numpy(dtype=float),
            "source_ring": frame["source_ring"].to_numpy(dtype=float),
            "source_surface": (
                (frame["source_core"] + frame["source_ring"]) / 2
            ).to_numpy(dtype=float),
            "source_anomaly": frame["source_anomaly"].to_numpy(dtype=float),
        }
    )
    normalized_hour = frame["target_hour_from_sunset"].to_numpy(dtype=float) / 6
    scene["hour_x_source_surface"] = normalized_hour * scene["source_surface"]
    scene["hour_x_source_anomaly"] = normalized_hour * scene["source_anomaly"]
    return pd.concat([hour.reset_index(drop=True), geometry, scene], axis=1)


def fit_hourly(frame: pd.DataFrame, mode: str):
    bias = (frame["target_anomaly"] - frame["source_anomaly"]).to_numpy()
    if mode == "raw":
        return {"mode": mode}
    if mode == "hour_offset":
        offsets = (
            pd.DataFrame(
                {"hour": frame["target_hour_from_sunset"].astype(int), "bias": bias}
            )
            .groupby("hour")["bias"]
            .mean()
            .to_dict()
        )
        return {"mode": mode, "offsets": offsets}
    features = hourly_features(frame, mode)
    if mode in ["geometry_ridge", "scene_ridge"]:
        model = Pipeline(
            [("scale", StandardScaler()), ("ridge", RidgeCV(alphas=RIDGE_ALPHAS))]
        )
    elif mode == "scene_gbdt":
        model = HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_iter=250,
            max_leaf_nodes=15,
            min_samples_leaf=35,
            l2_regularization=1.0,
            random_state=20260810,
        )
    else:
        raise ValueError(mode)
    model.fit(features, bias)
    return {"mode": mode, "model": model}


def predict_hourly(model, frame: pd.DataFrame) -> np.ndarray:
    mode = model["mode"]
    if mode == "raw":
        bias = np.zeros(len(frame))
    elif mode == "hour_offset":
        bias = (
            frame["target_hour_from_sunset"]
            .astype(int)
            .map(model["offsets"])
            .to_numpy(dtype=float)
        )
    else:
        bias = model["model"].predict(hourly_features(frame, mode))
    return frame["source_anomaly"].to_numpy(dtype=float) + bias


def transition_features(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[
        [
            "source_anomaly_transition",
            "source_core_transition",
            "source_ring_transition",
            "source_anomaly_pre",
            "source_anomaly_late",
            "source_surface_pre",
            "source_surface_late",
            "lat",
            "lon",
            "vza_target",
            "vza_source",
            "vza_difference",
            "vza_mean",
        ]
    ].astype(float)


def fit_transition(frame: pd.DataFrame, mode: str):
    bias = (
        frame["target_anomaly_transition"] - frame["source_anomaly_transition"]
    ).to_numpy()
    if mode == "raw":
        return {"mode": mode}
    if mode == "mean_offset":
        return {"mode": mode, "offset": float(bias.mean())}
    if mode == "transition_ridge":
        model = Pipeline(
            [("scale", StandardScaler()), ("ridge", RidgeCV(alphas=RIDGE_ALPHAS))]
        )
    elif mode == "transition_gbdt":
        model = HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_iter=200,
            max_leaf_nodes=12,
            min_samples_leaf=25,
            l2_regularization=1.0,
            random_state=20260810,
        )
    else:
        raise ValueError(mode)
    model.fit(transition_features(frame), bias)
    return {"mode": mode, "model": model}


def predict_transition(model, frame: pd.DataFrame) -> np.ndarray:
    mode = model["mode"]
    if mode == "raw":
        bias = np.zeros(len(frame))
    elif mode == "mean_offset":
        bias = np.repeat(model["offset"], len(frame))
    else:
        bias = model["model"].predict(transition_features(frame))
    return frame["source_anomaly_transition"].to_numpy(dtype=float) + bias


def score(target: np.ndarray, estimate: np.ndarray) -> dict[str, float]:
    error = estimate - target
    return {
        "mean_bias_k": float(error.mean()),
        "mae_k": float(np.abs(error).mean()),
        "rmse_k": float(np.sqrt(np.mean(error**2))),
        "ccc": ccc(target, estimate),
        "sign_disagreement": float(np.mean(np.sign(target) != np.sign(estimate))),
    }


def select_model(scores: pd.DataFrame, order: list[str]) -> pd.DataFrame:
    summary = scores.groupby("model").agg(
        mean_rmse_ratio=("rmse_ratio", "mean"),
        sd_rmse_ratio=("rmse_ratio", "std"),
        n_folds=("rmse_ratio", "size"),
    ).reset_index()
    summary["se_rmse_ratio"] = summary["sd_rmse_ratio"] / np.sqrt(summary["n_folds"])
    best = summary.loc[summary["mean_rmse_ratio"].idxmin()]
    threshold = best["mean_rmse_ratio"] + best["se_rmse_ratio"]
    eligible = set(summary.loc[summary["mean_rmse_ratio"].le(threshold), "model"])
    selected = next(model for model in order if model in eligible)
    summary["one_se_threshold"] = threshold
    summary["selected"] = summary["model"].eq(selected)
    return summary.sort_values("mean_rmse_ratio")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hourly = pd.read_parquet(BASE_OUT / "derivation_city_event_hourly.parquet")
    hourly = assign_spatial_blocks(hourly)
    raw_for_transition = hourly.copy()
    raw_for_transition["pred_core"] = raw_for_transition["source_core"]
    raw_for_transition["pred_ring"] = raw_for_transition["source_ring"]
    raw_for_transition["pred_anomaly"] = raw_for_transition["source_anomaly"]
    transitions = transition_frame(raw_for_transition)
    geometry = hourly[
        [
            "uc_id",
            "lat",
            "lon",
            "vza_target",
            "vza_source",
            "vza_difference",
            "vza_mean",
            "spatial_block",
        ]
    ].drop_duplicates("uc_id")
    transitions = transitions.merge(geometry, on="uc_id", how="left", validate="many_to_one")

    hourly_rows = []
    transition_rows = []
    hourly_predictions = []
    transition_predictions = []
    years = sorted(hourly["event_year"].unique())
    blocks = sorted(hourly["spatial_block"].unique())
    for year in years:
        for block in blocks:
            fold = f"year_{year}_block_{block}"
            h_test = hourly[
                hourly["event_year"].eq(year) & hourly["spatial_block"].eq(block)
            ].copy()
            h_train = hourly[
                hourly["event_year"].ne(year) & hourly["spatial_block"].ne(block)
            ].copy()
            t_test = transitions[
                transitions["event_year"].eq(year)
                & transitions["spatial_block"].eq(block)
            ].copy()
            t_train = transitions[
                transitions["event_year"].ne(year)
                & transitions["spatial_block"].ne(block)
            ].copy()
            raw_h_rmse = None
            for mode in HOURLY_MODELS:
                model = fit_hourly(h_train, mode)
                estimate = predict_hourly(model, h_test)
                metrics = score(h_test["target_anomaly"].to_numpy(), estimate)
                if mode == "raw":
                    raw_h_rmse = metrics["rmse_k"]
                hourly_rows.append(
                    {"fold": fold, "model": mode, **metrics}
                )
                hourly_predictions.append(
                    pd.DataFrame(
                        {
                            "uc_id": h_test["uc_id"].to_numpy(),
                            "event_year": h_test["event_year"].to_numpy(),
                            "event_time_id": h_test["event_time_id"].to_numpy(),
                            "target_hour_from_sunset": h_test[
                                "target_hour_from_sunset"
                            ].to_numpy(),
                            "fold": fold,
                            "model": mode,
                            "target": h_test["target_anomaly"].to_numpy(),
                            "estimate": estimate,
                        }
                    )
                )
            for row in hourly_rows[-len(HOURLY_MODELS):]:
                row["rmse_ratio"] = row["rmse_k"] / raw_h_rmse

            raw_t_rmse = None
            for mode in TRANSITION_MODELS:
                model = fit_transition(t_train, mode)
                estimate = predict_transition(model, t_test)
                metrics = score(t_test["target_anomaly_transition"].to_numpy(), estimate)
                if mode == "raw":
                    raw_t_rmse = metrics["rmse_k"]
                transition_rows.append(
                    {"fold": fold, "model": mode, **metrics}
                )
                transition_predictions.append(
                    pd.DataFrame(
                        {
                            "uc_id": t_test["uc_id"].to_numpy(),
                            "event_year": t_test["event_year"].to_numpy(),
                            "event_time_id": t_test["event_time_id"].to_numpy(),
                            "fold": fold,
                            "model": mode,
                            "target": t_test["target_anomaly_transition"].to_numpy(),
                            "estimate": estimate,
                        }
                    )
                )
            for row in transition_rows[-len(TRANSITION_MODELS):]:
                row["rmse_ratio"] = row["rmse_k"] / raw_t_rmse

    hourly_scores = pd.DataFrame(hourly_rows)
    transition_scores = pd.DataFrame(transition_rows)
    hourly_selection = select_model(hourly_scores, HOURLY_MODELS)
    transition_selection = select_model(transition_scores, TRANSITION_MODELS)
    hourly_scores.to_csv(OUT / "hourly_cross_validation_scores.csv", index=False)
    transition_scores.to_csv(OUT / "transition_cross_validation_scores.csv", index=False)
    hourly_selection.to_csv(OUT / "hourly_model_selection.csv", index=False)
    transition_selection.to_csv(OUT / "transition_model_selection.csv", index=False)
    pd.concat(hourly_predictions, ignore_index=True).to_parquet(
        OUT / "hourly_cross_validated_predictions.parquet", index=False
    )
    pd.concat(transition_predictions, ignore_index=True).to_parquet(
        OUT / "transition_cross_validated_predictions.parquet", index=False
    )
    print("Hourly selection")
    print(hourly_selection.to_string(index=False))
    print("\nTransition selection")
    print(transition_selection.to_string(index=False))


if __name__ == "__main__":
    main()
