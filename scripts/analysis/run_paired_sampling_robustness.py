from pathlib import Path

import numpy as np
import pandas as pd

from analysis_utils import twfe_cluster_ols
from run_diurnal_inversion_mechanism import build_storage_score


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/external/valid_city_interval_panel.parquet"
OUT = ROOT / "data/processed/analysis_outputs/paired_sampling_robustness.csv"


def prepare() -> pd.DataFrame:
    columns = [
        "uc_id",
        "time_id",
        "analysis_state",
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
        "core_n_built_day",
        "ring_n_built_day",
        "core_n_built_night",
        "ring_n_built_night",
    ]
    frame = pd.read_parquet(PANEL, columns=columns)
    frame["raw_day_contrast"] = frame["core_tb_day"] - frame["ring_tb_day"]
    frame["raw_night_contrast"] = frame["core_tb_night"] - frame["ring_tb_night"]
    frame["day_anomaly_contrast"] = frame["core_tb_day_anom"] - frame["ring_tb_day_anom"]
    frame["night_anomaly_contrast"] = frame["core_tb_night_anom"] - frame["ring_tb_night_anom"]
    frame["is_dhd"] = frame["analysis_state"].eq("dhd").astype(float)
    frame["is_extreme_dhd"] = frame["analysis_state"].eq("extreme_dhd").astype(float)
    for column in ["t2m_true_night_pct_rank", "vpd_pct", "rzsm_pct"]:
        frame[f"z_{column}"] = (frame[column] - frame[column].mean()) / frame[column].std(ddof=0)
    return frame


def main() -> None:
    frame = prepare()
    city, _ = build_storage_score()
    frame = frame.merge(
        city[["uc_id", "built_form_storage_score"]], on="uc_id", how="left", validate="many_to_one"
    )
    frame["dhd_x_storage"] = frame["is_dhd"] * frame["built_form_storage_score"]
    frame["extreme_x_storage"] = frame["is_extreme_dhd"] * frame["built_form_storage_score"]
    paired = [
        "raw_day_contrast",
        "raw_night_contrast",
        "day_anomaly_contrast",
        "night_anomaly_contrast",
    ]
    support = [
        "core_n_built_day",
        "ring_n_built_day",
        "core_n_built_night",
        "ring_n_built_night",
    ]
    screens = {
        "base_valid_paired": frame[paired].notna().all(axis=1),
        "all_units_at_least_10_built_pixels": frame[paired].notna().all(axis=1)
        & frame[support].ge(10).all(axis=1),
        "all_units_at_least_20_built_pixels": frame[paired].notna().all(axis=1)
        & frame[support].ge(20).all(axis=1),
    }
    rows = []
    for name, mask in screens.items():
        subset = frame[
            mask & frame["high_green"].eq(1) & frame["analysis_state"].isin(["mld", "dhd", "extreme_dhd"])
        ].copy()
        model = twfe_cluster_ols(
            subset,
            "raw_night_contrast",
            [
                "raw_day_contrast",
                "is_dhd",
                "is_extreme_dhd",
                "z_t2m_true_night_pct_rank",
                "z_vpd_pct",
                "z_rzsm_pct",
                "dhd_x_storage",
                "extreme_x_storage",
            ],
            model_name=name,
        )
        for term in ["dhd_x_storage", "extreme_x_storage"]:
            row = model[model["term"].eq(term)].iloc[0].to_dict()
            row["screen"] = name
            row["minimum_built_pixels"] = {"base_valid_paired": 5, "all_units_at_least_10_built_pixels": 10, "all_units_at_least_20_built_pixels": 20}[name]
            rows.append(row)
    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False)
    print(result[["screen", "term", "estimate", "ci95_low", "ci95_high", "n_obs", "n_cities"]].round(5).to_string(index=False))


if __name__ == "__main__":
    main()
