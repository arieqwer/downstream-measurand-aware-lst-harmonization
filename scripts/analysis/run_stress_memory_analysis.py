from pathlib import Path

import numpy as np
import pandas as pd

from analysis_utils import holm_adjust, twfe_cluster_ols
from run_diurnal_inversion_mechanism import build_storage_score


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/external/valid_city_interval_panel.parquet"
SOURCE = ROOT / "data/external/dhd_stress_history_panel.parquet"
OUT = ROOT / "data/processed/analysis_outputs"
INVERSION_THRESHOLDS = [0.0, 0.1, 0.25, 0.5]
OVERPASS_SEPARATION_HOURS = 12.0


def stress_history() -> pd.DataFrame:
    history = pd.read_parquet(SOURCE, columns=["uc_id", "time_id", "dhd"])
    history["uc_id"] = history["uc_id"].astype(str)
    history = history.sort_values(["uc_id", "time_id"]).copy()
    history["dhd"] = history["dhd"].astype(bool)
    grouped = history.groupby("uc_id", sort=False)
    previous_time = grouped["time_id"].shift()
    start = history["dhd"] & (
        ~grouped["dhd"].shift(fill_value=False) | history["time_id"].sub(previous_time).ne(1)
    )
    history["run_group"] = start.groupby(history["uc_id"]).cumsum()
    history["dhd_run_length"] = 0
    dhd_rows = history["dhd"]
    history.loc[dhd_rows, "dhd_run_length"] = (
        history.loc[dhd_rows]
        .groupby(["uc_id", "run_group"], sort=False)
        .cumcount()
        .add(1)
        .to_numpy()
    )
    for lag in range(1, 5):
        lag_state = grouped["dhd"].shift(lag)
        lag_time = grouped["time_id"].shift(lag)
        history[f"lag{lag}_dhd"] = lag_state.where(
            history["time_id"].sub(lag_time).eq(lag)
        ).fillna(False).astype(bool)

    current_non_dhd = ~history["dhd"]
    for lag in range(1, 5):
        no_more_recent = np.ones(len(history), dtype=bool)
        for recent in range(1, lag):
            no_more_recent &= ~history[f"lag{recent}_dhd"].to_numpy()
        history[f"post_dhd_lag{lag}"] = (
            current_non_dhd.to_numpy() & no_more_recent & history[f"lag{lag}_dhd"].to_numpy()
        ).astype(float)
    return history[
        [
            "uc_id",
            "time_id",
            "dhd_run_length",
            *[f"post_dhd_lag{lag}" for lag in range(1, 5)],
        ]
    ]


def prepare_panel() -> pd.DataFrame:
    columns = [
        "uc_id",
        "time_id",
        "analysis_state",
        "dhd",
        "high_green",
        "t2m_true_night_pct_rank",
        "vpd_pct",
        "rzsm_pct",
        "core_tb_day",
        "ring_tb_day",
        "core_tb_night",
        "ring_tb_night",
        "core_tb_day_anom",
        "ring_tb_day_anom",
        "core_tb_night_anom",
        "ring_tb_night_anom",
    ]
    frame = pd.read_parquet(PANEL, columns=columns)
    frame["raw_day_contrast"] = frame["core_tb_day"] - frame["ring_tb_day"]
    frame["raw_night_contrast"] = frame["core_tb_night"] - frame["ring_tb_night"]
    frame["day_anomaly_contrast"] = frame["core_tb_day_anom"] - frame["ring_tb_day_anom"]
    frame["night_anomaly_contrast"] = frame["core_tb_night_anom"] - frame["ring_tb_night_anom"]
    core_decay = np.log((frame["core_tb_day"] + 273.15) / (frame["core_tb_night"] + 273.15))
    ring_decay = np.log((frame["ring_tb_day"] + 273.15) / (frame["ring_tb_night"] + 273.15))
    frame["differential_decay_1e4_h"] = (
        (core_decay - ring_decay) / OVERPASS_SEPARATION_HOURS
    ) * 1e4
    for threshold in INVERSION_THRESHOLDS:
        label = str(threshold).replace(".", "p")
        frame[f"inversion_{label}"] = (
            frame["day_anomaly_contrast"].lt(-threshold)
            & frame["night_anomaly_contrast"].gt(threshold)
        ).astype(float)
    for column in ["t2m_true_night_pct_rank", "vpd_pct", "rzsm_pct"]:
        frame[f"z_{column}"] = (frame[column] - frame[column].mean()) / frame[column].std(ddof=0)
    return frame.merge(stress_history(), on=["uc_id", "time_id"], how="left", validate="one_to_one")


def main() -> None:
    frame = prepare_panel()
    city, _ = build_storage_score()
    high = frame[frame["high_green"].eq(1)].merge(
        city[["uc_id", "built_form_storage_score"]], on="uc_id", how="left", validate="many_to_one"
    )
    controls = ["z_t2m_true_night_pct_rank", "z_vpd_pct", "z_rzsm_pct"]
    rows = []

    within_dhd = high[high["dhd"].eq(1)].copy()
    within_dhd["duration_excess_capped"] = (within_dhd["dhd_run_length"] - 1).clip(0, 5)
    within_dhd["duration_x_storage"] = (
        within_dhd["duration_excess_capped"] * within_dhd["built_form_storage_score"]
    )
    duration_outcomes = [
        ("raw_night_contrast", "raw_day_contrast"),
        ("night_anomaly_contrast", "day_anomaly_contrast"),
        ("differential_decay_1e4_h", None),
        *[(f"inversion_{str(value).replace('.', 'p')}", None) for value in INVERSION_THRESHOLDS],
    ]
    for outcome, daytime in duration_outcomes:
        predictors = [*controls, "duration_excess_capped", "duration_x_storage"]
        if daytime is not None:
            predictors.insert(0, daytime)
        rows.append(
            twfe_cluster_ols(
                within_dhd,
                outcome,
                predictors,
                model_name=f"dhd_duration_{outcome}",
            )
        )

    recovery = high[high["dhd"].eq(0)].copy()
    for lag in range(1, 5):
        recovery[f"post_dhd_lag{lag}_x_storage"] = (
            recovery[f"post_dhd_lag{lag}"] * recovery["built_form_storage_score"]
        )
    post_terms = [f"post_dhd_lag{lag}" for lag in range(1, 5)]
    post_interactions = [f"post_dhd_lag{lag}_x_storage" for lag in range(1, 5)]
    recovery_outcomes = [
        ("raw_night_contrast", "raw_day_contrast"),
        ("night_anomaly_contrast", "day_anomaly_contrast"),
        ("differential_decay_1e4_h", None),
        *[(f"inversion_{str(value).replace('.', 'p')}", None) for value in INVERSION_THRESHOLDS],
    ]
    for outcome, daytime in recovery_outcomes:
        predictors = [*controls, *post_terms, *post_interactions]
        if daytime is not None:
            predictors.insert(0, daytime)
        rows.append(
            twfe_cluster_ols(
                recovery,
                outcome,
                predictors,
                model_name=f"post_dhd_memory_{outcome}",
            )
        )

    model_terms = pd.concat(rows, ignore_index=True)
    model_terms["p_value_holm_within_model"] = model_terms.groupby("model")["p_value"].transform(
        holm_adjust
    )
    model_terms.to_csv(OUT / "stress_memory_twfe_terms.csv", index=False)
    key = model_terms[
        model_terms["term"].str.contains("duration|post_dhd", regex=True)
    ]
    print(key.round(5).to_string(index=False))


if __name__ == "__main__":
    main()
