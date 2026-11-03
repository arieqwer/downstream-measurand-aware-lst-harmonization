from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from run_multiplatform_harmonization import RIDGE_ALPHAS, ccc, transition_frame
from screen_metric_aware_harmonization import hourly_features, transition_features


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "outputs/grl_deepening_2026/multiplatform_expanded_validation/combined_2025_common_domain_predictions.parquet"
)
OUT = ROOT / "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization"
PROTOCOL = ROOT / "goes18_goes19_metric_aware_harmonization_protocol.md"
MODEL_PATH = OUT / "frozen_metric_aware_model.joblib"
HOURLY_ORDER = ["raw", "hour_offset", "geometry_ridge", "scene_gbdt"]
TRANSITION_ORDER = ["raw", "mean_offset", "transition_ridge", "transition_gbdt"]
SEED = 20260810


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assign_blocks(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    cities = (
        result[["uc_id", "lon"]]
        .drop_duplicates("uc_id")
        .sort_values(["lon", "uc_id"])
        .reset_index(drop=True)
    )
    cities["spatial_block"] = np.floor(np.arange(len(cities)) * 5 / len(cities)).astype(int)
    events = pd.DataFrame({"event_time_id": sorted(result["event_time_id"].unique())})
    events["event_block"] = np.floor(np.arange(len(events)) * 5 / len(events)).astype(int)
    return (
        result.merge(cities[["uc_id", "spatial_block"]], on="uc_id", validate="many_to_one")
        .merge(events, on="event_time_id", validate="many_to_one")
    )


def fit_hourly(frame: pd.DataFrame, model_name: str, component: str) -> dict:
    bias = (frame[f"target_{component}"] - frame[f"source_{component}"]).to_numpy()
    if model_name == "raw":
        return {"name": model_name, "component": component}
    if model_name == "hour_offset":
        offsets = (
            pd.DataFrame(
                {"hour": frame["target_hour_from_sunset"].astype(int), "bias": bias}
            )
            .groupby("hour")["bias"]
            .mean()
            .to_dict()
        )
        return {"name": model_name, "component": component, "offsets": offsets}
    if model_name == "geometry_ridge":
        features = hourly_features(frame, "geometry_ridge")
        estimator = Pipeline(
            [("scale", StandardScaler()), ("ridge", RidgeCV(alphas=RIDGE_ALPHAS))]
        )
    elif model_name == "scene_gbdt":
        features = hourly_features(frame, "scene_gbdt")
        estimator = HistGradientBoostingRegressor(
            learning_rate=0.04,
            max_iter=300,
            max_leaf_nodes=15,
            min_samples_leaf=35,
            l2_regularization=2.0,
            random_state=SEED,
        )
    else:
        raise ValueError(model_name)
    estimator.fit(features, bias)
    return {"name": model_name, "component": component, "estimator": estimator}


def predict_hourly(model: dict, frame: pd.DataFrame) -> np.ndarray:
    name = model["name"]
    component = model["component"]
    if name == "raw":
        correction = np.zeros(len(frame))
    elif name == "hour_offset":
        correction = (
            frame["target_hour_from_sunset"]
            .astype(int)
            .map(model["offsets"])
            .to_numpy(dtype=float)
        )
    elif name == "geometry_ridge":
        correction = model["estimator"].predict(hourly_features(frame, "geometry_ridge"))
    elif name == "scene_gbdt":
        correction = model["estimator"].predict(hourly_features(frame, "scene_gbdt"))
    else:
        raise ValueError(name)
    return frame[f"source_{component}"].to_numpy(dtype=float) + correction


def fit_transition(frame: pd.DataFrame, model_name: str) -> dict:
    bias = (
        frame["target_anomaly_transition"] - frame["source_anomaly_transition"]
    ).to_numpy()
    if model_name == "raw":
        return {"name": model_name}
    if model_name == "mean_offset":
        return {"name": model_name, "offset": float(bias.mean())}
    features = transition_features(frame)
    if model_name == "transition_ridge":
        estimator = Pipeline(
            [("scale", StandardScaler()), ("ridge", RidgeCV(alphas=RIDGE_ALPHAS))]
        )
    elif model_name == "transition_gbdt":
        estimator = HistGradientBoostingRegressor(
            learning_rate=0.04,
            max_iter=250,
            max_leaf_nodes=12,
            min_samples_leaf=25,
            l2_regularization=2.0,
            random_state=SEED,
        )
    else:
        raise ValueError(model_name)
    estimator.fit(features, bias)
    return {"name": model_name, "estimator": estimator}


def predict_transition(model: dict, frame: pd.DataFrame) -> np.ndarray:
    if model["name"] == "raw":
        correction = np.zeros(len(frame))
    elif model["name"] == "mean_offset":
        correction = np.repeat(model["offset"], len(frame))
    else:
        correction = model["estimator"].predict(transition_features(frame))
    return frame["source_anomaly_transition"].to_numpy(dtype=float) + correction


def score(target: np.ndarray, estimate: np.ndarray) -> dict[str, float]:
    error = estimate - target
    return {
        "mean_bias_k": float(error.mean()),
        "mae_k": float(np.abs(error).mean()),
        "rmse_k": float(np.sqrt(np.mean(error**2))),
        "ccc": ccc(target, estimate),
        "sign_disagreement": float(np.mean(np.sign(target) != np.sign(estimate))),
    }


def selection(scores: pd.DataFrame, order: list[str]) -> tuple[pd.DataFrame, str]:
    summary = scores.groupby("model").agg(
        mean_rmse_ratio=("rmse_ratio", "mean"),
        sd_rmse_ratio=("rmse_ratio", "std"),
        n_folds=("rmse_ratio", "size"),
    ).reset_index()
    summary["se_rmse_ratio"] = summary["sd_rmse_ratio"] / np.sqrt(summary["n_folds"])
    best = summary.loc[summary["mean_rmse_ratio"].idxmin()]
    threshold = float(best["mean_rmse_ratio"] + best["se_rmse_ratio"])
    eligible = set(summary.loc[summary["mean_rmse_ratio"].le(threshold), "model"])
    selected = next(item for item in order if item in eligible)
    summary["one_se_threshold"] = threshold
    summary["selected"] = summary["model"].eq(selected)
    return summary.sort_values("mean_rmse_ratio"), selected


def prepare_transition(hourly: pd.DataFrame) -> pd.DataFrame:
    base = hourly.copy()
    base["pred_core"] = base["source_core"]
    base["pred_ring"] = base["source_ring"]
    base["pred_anomaly"] = base["source_anomaly"]
    event = transition_frame(base)
    geometry = hourly[
        [
            "uc_id",
            "event_time_id",
            "lat",
            "lon",
            "vza_target",
            "vza_source",
            "vza_difference",
            "vza_mean",
            "spatial_block",
            "event_block",
        ]
    ].drop_duplicates(["uc_id", "event_time_id"])
    return event.merge(
        geometry,
        on=["uc_id", "event_time_id"],
        how="left",
        validate="one_to_one",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hourly = assign_blocks(pd.read_parquet(SOURCE))
    transitions = prepare_transition(hourly)
    hourly_scores = []
    transition_scores = []
    hourly_oof = []
    transition_oof = []
    for spatial in sorted(hourly["spatial_block"].unique()):
        for event_block in sorted(hourly["event_block"].unique()):
            fold = f"spatial_{spatial}_event_{event_block}"
            test_rule_h = hourly["spatial_block"].eq(spatial) & hourly["event_block"].eq(event_block)
            train_rule_h = hourly["spatial_block"].ne(spatial) & hourly["event_block"].ne(event_block)
            h_train = hourly[train_rule_h]
            h_test = hourly[test_rule_h]
            test_rule_t = transitions["spatial_block"].eq(spatial) & transitions["event_block"].eq(event_block)
            train_rule_t = transitions["spatial_block"].ne(spatial) & transitions["event_block"].ne(event_block)
            t_train = transitions[train_rule_t]
            t_test = transitions[test_rule_t]
            for component in ["core", "ring", "anomaly"]:
                fold_rows = []
                raw_rmse = None
                for model_name in HOURLY_ORDER:
                    model = fit_hourly(h_train, model_name, component)
                    estimate = predict_hourly(model, h_test)
                    metrics = score(h_test[f"target_{component}"].to_numpy(), estimate)
                    if model_name == "raw":
                        raw_rmse = metrics["rmse_k"]
                    fold_rows.append(
                        {
                            "fold": fold,
                            "component": component,
                            "model": model_name,
                            **metrics,
                        }
                    )
                    hourly_oof.append(
                        pd.DataFrame(
                            {
                                "uc_id": h_test["uc_id"].to_numpy(),
                                "event_time_id": h_test["event_time_id"].to_numpy(),
                                "target_hour_from_sunset": h_test[
                                    "target_hour_from_sunset"
                                ].to_numpy(),
                                "fold": fold,
                                "component": component,
                                "model": model_name,
                                "target": h_test[f"target_{component}"].to_numpy(),
                                "estimate": estimate,
                            }
                        )
                    )
                for row in fold_rows:
                    row["rmse_ratio"] = row["rmse_k"] / raw_rmse
                hourly_scores.extend(fold_rows)

            fold_rows = []
            raw_rmse = None
            for model_name in TRANSITION_ORDER:
                model = fit_transition(t_train, model_name)
                estimate = predict_transition(model, t_test)
                metrics = score(t_test["target_anomaly_transition"].to_numpy(), estimate)
                if model_name == "raw":
                    raw_rmse = metrics["rmse_k"]
                fold_rows.append({"fold": fold, "model": model_name, **metrics})
                transition_oof.append(
                    pd.DataFrame(
                        {
                            "uc_id": t_test["uc_id"].to_numpy(),
                            "event_time_id": t_test["event_time_id"].to_numpy(),
                            "fold": fold,
                            "model": model_name,
                            "target": t_test["target_anomaly_transition"].to_numpy(),
                            "estimate": estimate,
                        }
                    )
                )
            for row in fold_rows:
                row["rmse_ratio"] = row["rmse_k"] / raw_rmse
            transition_scores.extend(fold_rows)

    hourly_scores = pd.DataFrame(hourly_scores)
    transition_scores = pd.DataFrame(transition_scores)
    hourly_oof = pd.concat(hourly_oof, ignore_index=True)
    transition_oof = pd.concat(transition_oof, ignore_index=True)
    selected_hourly = {}
    selection_frames = []
    final_models = {"hourly": {}}
    for component in ["core", "ring", "anomaly"]:
        summary, selected = selection(
            hourly_scores[hourly_scores["component"].eq(component)], HOURLY_ORDER
        )
        summary["outcome"] = f"hourly_{component}"
        selection_frames.append(summary)
        selected_hourly[component] = selected
        final_models["hourly"][component] = fit_hourly(hourly, selected, component)
    transition_summary, selected_transition = selection(
        transition_scores, TRANSITION_ORDER
    )
    transition_summary["outcome"] = "anomaly_transition"
    selection_frames.append(transition_summary)
    final_models["transition"] = fit_transition(transitions, selected_transition)

    selected_oof = transition_oof[
        transition_oof["model"].eq(selected_transition)
    ].copy()
    absolute_residual = np.abs(selected_oof["estimate"] - selected_oof["target"])
    q90 = float(absolute_residual.quantile(0.9, interpolation="higher"))
    final_models["transition_uncertainty_half_width_k"] = q90
    final_models["training_target_sensor"] = "GOES18"
    final_models["training_source_sensor"] = "GOES19"
    joblib.dump(final_models, MODEL_PATH)

    hourly_scores.to_csv(OUT / "hourly_cross_validation_scores.csv", index=False)
    transition_scores.to_csv(OUT / "transition_cross_validation_scores.csv", index=False)
    hourly_oof.to_parquet(OUT / "hourly_cross_validated_predictions.parquet", index=False)
    transition_oof.to_parquet(OUT / "transition_cross_validated_predictions.parquet", index=False)
    selections = pd.concat(selection_frames, ignore_index=True)
    selections.to_csv(OUT / "model_selection.csv", index=False)
    manifest = {
        "stage": "2025_calibration_complete_2026_not_opened",
        "protocol_sha256": sha256(PROTOCOL),
        "source_sha256": sha256(SOURCE),
        "model_sha256": sha256(MODEL_PATH),
        "n_hourly": int(len(hourly)),
        "n_transitions": int(len(transitions)),
        "n_cities": int(hourly["uc_id"].nunique()),
        "n_intervals": int(hourly["event_time_id"].nunique()),
        "selected_hourly_models": selected_hourly,
        "selected_transition_model": selected_transition,
        "transition_uncertainty_half_width_k": q90,
        "selection": selections.to_dict(orient="records"),
    }
    (OUT / "frozen_metric_aware_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
