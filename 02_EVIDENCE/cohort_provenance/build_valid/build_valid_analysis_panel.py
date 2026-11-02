from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path("/Users/apple/Downloads/nbs")
SOURCE_PANEL = (
    ROOT
    / "rerun_repair/extended_outputs_local/23_true_night_green_refuge_failure/"
    "true_night_green_refuge_failure_panel.parquet"
)
RAW_PANEL = Path("/Users/apple/Downloads/TRC_threshold_analysis_panel_anom_corrected.parquet")
CITY_BASE = (
    ROOT
    / "nature-cities-green-refuge-reliability/data/processed/metadata/"
    "panel_city_base_corrected.csv"
)
OUT = ROOT / "reliability_dynamics_upgrade"


def state_name(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(
        np.select(
            [frame["extreme_dhd"].eq(1), frame["dhd"].eq(1), frame["mld"].eq(1)],
            ["extreme_dhd", "dhd", "mld"],
            default="other",
        ),
        index=frame.index,
    )


def load_raw_interval_components() -> pd.DataFrame:
    keys = ["uc_id", "year", "step8"]
    metrics = [
        "tb_day",
        "tb_night",
        "tv_day",
        "tv_night",
        "tb_day_anom",
        "tb_night_anom",
        "tv_day_anom",
        "tv_night_anom",
    ]
    support_metrics = [
        "n_obs_day",
        "n_obs_night",
        "n_built_day",
        "n_built_night",
        "n_veg_day",
        "n_veg_night",
    ]
    climate = ["t2m_c", "vpd_kpa", "rzsm", "pr_sum"]

    core = pq.read_table(
        RAW_PANEL,
        columns=[*keys, "unit", *metrics, *support_metrics, *climate],
        filters=[("unit", "=", "core")],
    ).to_pandas()
    core["uc_id"] = core["uc_id"].astype(str)
    core = core.drop(columns="unit").rename(
        columns={metric: f"core_{metric}" for metric in [*metrics, *support_metrics]}
    )

    ring = pq.read_table(
        RAW_PANEL,
        columns=[*keys, "unit", *metrics, *support_metrics],
        filters=[("unit", "=", "ring10_20")],
    ).to_pandas()
    ring["uc_id"] = ring["uc_id"].astype(str)
    ring = ring.drop(columns="unit").rename(
        columns={metric: f"ring_{metric}" for metric in [*metrics, *support_metrics]}
    )

    raw = core.merge(ring, on=keys, how="left", validate="one_to_one")
    raw["log1p_pr_sum"] = np.log1p(raw["pr_sum"].clip(lower=0))
    for metric in metrics:
        raw[f"raw_core_minus_ring_{metric}"] = raw[f"core_{metric}"] - raw[f"ring_{metric}"]
    return raw


def summarize_raw_climate(raw: pd.DataFrame) -> pd.DataFrame:
    return (
        raw.groupby("uc_id", as_index=False)
        .agg(
            mean_t2m_c=("t2m_c", "mean"),
            mean_vpd_kpa=("vpd_kpa", "mean"),
            mean_rzsm=("rzsm", "mean"),
            mean_log1p_pr_sum=("log1p_pr_sum", "mean"),
        )
    )


def main() -> None:
    panel_columns = [
        "uc_id",
        "veg_group",
        "year",
        "step8",
        "time_id",
        "state",
        "dhd",
        "mld",
        "extreme_dhd",
        "rzsm_pct",
        "vpd_pct",
        "t2m_true_night_pct_rank",
        "t2m_true_night_c",
        "wetbulb_true_night_c",
        "heat_true_night_t2m_local_p90",
        "core_minus_ring_tb_night_anom",
        "anomalous_core_warmer",
        "population_2025",
        "un_sdg_reg",
        "wb_income",
        "period",
    ]
    source = pd.read_parquet(SOURCE_PANEL, columns=panel_columns)
    source["uc_id"] = source["uc_id"].astype(str)
    source["analysis_state"] = state_name(source)
    source["valid_core_ring"] = source["core_minus_ring_tb_night_anom"].notna()

    valid = source[source["valid_core_ring"]].copy()
    valid["loss_state"] = valid["core_minus_ring_tb_night_anom"].gt(0).astype("int8")
    valid["high_green"] = valid["veg_group"].eq("high_veg").astype("int8")

    raw_interval = load_raw_interval_components()
    valid = valid.merge(raw_interval, on=["uc_id", "year", "step8"], how="left", validate="one_to_one")

    city_base = pd.read_csv(CITY_BASE, dtype={"uc_id": str})[["uc_id", "mean_ring_veg"]]
    valid = valid.merge(city_base, on="uc_id", how="left", validate="many_to_one")
    valid["z_ring_green_support"] = (
        valid["mean_ring_veg"] - city_base["mean_ring_veg"].mean()
    ) / city_base["mean_ring_veg"].std(ddof=0)

    source_counts = source.groupby("uc_id", as_index=False).agg(n_source_intervals=("time_id", "size"))
    city = (
        valid.groupby("uc_id", as_index=False)
        .agg(
            veg_group=("veg_group", "first"),
            high_green=("high_green", "first"),
            population_2025=("population_2025", "first"),
            un_sdg_reg=("un_sdg_reg", "first"),
            wb_income=("wb_income", "first"),
            mean_ring_veg=("mean_ring_veg", "first"),
            z_ring_green_support=("z_ring_green_support", "first"),
            n_valid_intervals=("time_id", "size"),
            median_true_night_t2m_c=("t2m_true_night_c", "median"),
            median_true_night_wetbulb_c=("wetbulb_true_night_c", "median"),
            true_night_heat_share=("heat_true_night_t2m_local_p90", "mean"),
        )
        .merge(source_counts, on="uc_id", how="left", validate="one_to_one")
    )
    city["valid_core_ring_fraction"] = city["n_valid_intervals"] / city["n_source_intervals"]
    city["log_population"] = np.log(city["population_2025"].clip(lower=1))

    state_city = (
        valid[valid["analysis_state"].isin(["mld", "dhd", "extreme_dhd"])]
        .groupby(["uc_id", "analysis_state"], as_index=False)
        .agg(
            n_state=("time_id", "size"),
            mean_gradient=("core_minus_ring_tb_night_anom", "mean"),
            loss_probability=("loss_state", "mean"),
        )
    )
    for state in ["mld", "dhd", "extreme_dhd"]:
        state_part = state_city[state_city["analysis_state"].eq(state)].drop(columns="analysis_state")
        state_part = state_part.rename(
            columns={
                "n_state": f"n_{state}",
                "mean_gradient": f"mean_gradient_{state}",
                "loss_probability": f"loss_probability_{state}",
            }
        )
        city = city.merge(state_part, on="uc_id", how="left", validate="one_to_one")

    city = city.merge(summarize_raw_climate(raw_interval), on="uc_id", how="left", validate="one_to_one")

    audit = (
        source.groupby(["veg_group", "analysis_state"], as_index=False)
        .agg(
            n_source_intervals=("time_id", "size"),
            n_valid_core_ring=("valid_core_ring", "sum"),
        )
    )
    audit["valid_fraction"] = audit["n_valid_core_ring"] / audit["n_source_intervals"]

    mismatch = (
        valid["loss_state"].astype(int).to_numpy()
        != valid["anomalous_core_warmer"].astype(int).to_numpy()
    ).sum()
    if mismatch:
        raise RuntimeError(f"Found {mismatch} valid rows with inconsistent binary and continuous outcomes")

    data_dir = OUT / "data"
    output_dir = OUT / "outputs"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    valid.sort_values(["uc_id", "time_id"]).to_parquet(
        data_dir / "valid_city_interval_panel.parquet", index=False, compression="zstd"
    )
    city.to_csv(data_dir / "city_covariates.csv", index=False)
    audit.to_csv(output_dir / "observation_validity_audit.csv", index=False)

    print(f"Source rows: {len(source):,}")
    print(f"Valid core-ring rows: {len(valid):,}")
    print(f"Excluded rows with missing core-ring outcome: {len(source) - len(valid):,}")
    print(audit.to_string(index=False))


if __name__ == "__main__":
    main()
