from __future__ import annotations

import json
from pathlib import Path

import ee
import pandas as pd
import pyarrow.dataset as ds
from sklearn.decomposition import PCA


ROOT = Path(__file__).resolve().parents[1]
UPGRADE = ROOT.parent / "reliability_dynamics_upgrade"
OUT = ROOT / "data/goes_sunset_confirmation"
OUT.mkdir(parents=True, exist_ok=True)

PANEL = UPGRADE / "data/valid_city_interval_panel.parquet"
PANEL_CITIES = UPGRADE / "data/city_covariates.csv"
LOCATIONS = UPGRADE / "figure_source_data/figure_1a_city_locations.csv"
EXTERNAL = Path(
    "/Users/apple/Downloads/nbs/rerun_repair/extended_outputs_local/"
    "64_external_process_validation_models/external_process_validation_city_table.csv"
)
PILOT = ROOT / "data/goes_sunset_pilot/goes_sunset_pilot_cities.csv"
PILOT_INTERVALS = ROOT / "data/goes_sunset_pilot/goes_sunset_pilot_intervals.csv"
UCDB_ASSET = "projects/ee-zuruyuyu/assets/ucdb_uc_polygons_fixed_all"
EE_PROJECT = "ee-zuruyuyu"
FEATURES = [
    "built_surface_fraction_2020",
    "mean_building_height_2020",
    "road_density_2024",
    "lcz_compact_share_2025",
]
RANDOM_SEED = 20260805


def select_cities() -> pd.DataFrame:
    panel = pd.read_csv(PANEL_CITIES, dtype={"uc_id": str})
    panel = panel[panel["high_green"].eq(1)][["uc_id"]]
    city = pd.read_csv(EXTERNAL, dtype={"uc_id": str})
    city = panel.merge(city, on="uc_id", how="inner", validate="one_to_one")
    complete = city[FEATURES].notna().all(axis=1) & city[
        "mean_water_support_ratio"
    ].notna()
    city = city.loc[complete].copy()

    standardized = (city[FEATURES] - city[FEATURES].mean()) / city[FEATURES].std(
        ddof=0
    )
    score = PCA(n_components=1, random_state=RANDOM_SEED).fit_transform(
        standardized
    ).ravel()
    if pd.Series(score).corr(standardized.mean(axis=1).reset_index(drop=True)) < 0:
        score *= -1
    city["heat_retention_score"] = score
    city["water_tertile"] = pd.qcut(
        city["mean_water_support_ratio"],
        3,
        labels=["Low", "Intermediate", "High"],
    )
    city["storage_quartile"] = pd.qcut(
        city["heat_retention_score"], 4, labels=[1, 2, 3, 4]
    )

    locations = pd.read_csv(LOCATIONS, dtype={"uc_id": str})
    city = city.merge(locations[["uc_id", "lat", "lon"]], on="uc_id", how="inner")
    pilot_ids = set(pd.read_csv(PILOT, dtype={"uc_id": str})["uc_id"])
    city = city[
        city["un_sdg_reg"].eq("Northern America")
        & city["lon"].between(-125.0, -66.0)
        & city["lat"].between(24.0, 50.0)
        & ~city["uc_id"].isin(pilot_ids)
    ].copy()
    city["profile"] = "intermediate"
    city.loc[
        city["water_tertile"].eq("Low")
        & city["storage_quartile"].eq(4),
        "profile",
    ] = "lower-water/higher-built"
    city.loc[
        city["water_tertile"].eq("High")
        & city["storage_quartile"].eq(1),
        "profile",
    ] = "higher-water/lower-built"
    keep = [
        "uc_id",
        "un_sdg_reg",
        "water_tertile",
        "storage_quartile",
        "mean_water_support_ratio",
        "heat_retention_score",
        "profile",
        "lat",
        "lon",
    ]
    return city[keep].sort_values("uc_id").reset_index(drop=True)


def load_city_events(cities: pd.DataFrame, intervals: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "uc_id",
        "year",
        "step8",
        "time_id",
        "rzsm_pct",
        "vpd_pct",
        "t2m_true_night_pct_rank",
        "t2m_true_night_c",
    ]
    frame = ds.dataset(PANEL, format="parquet").to_table(columns=columns).to_pandas()
    frame["uc_id"] = frame["uc_id"].astype(str)
    selected = intervals[["year", "step8", "time_id", "start_date", "end_date"]]
    frame = frame[
        frame["uc_id"].isin(cities["uc_id"])
        & frame["year"].between(2018, 2024)
    ].merge(selected, on=["year", "step8", "time_id"], how="inner")
    frame["hydroclimatic_severity"] = (
        (100.0 - frame["rzsm_pct"]) + frame["vpd_pct"]
    ) / 2.0
    frame["true_night_heat"] = frame["t2m_true_night_pct_rank"].ge(90.0)
    frame["severe_hot"] = frame["true_night_heat"] & frame[
        "hydroclimatic_severity"
    ].ge(85.0)
    frame["lower_severity_hot"] = frame["true_night_heat"] & frame[
        "hydroclimatic_severity"
    ].le(50.0)
    return frame.merge(cities, on="uc_id", how="inner", validate="many_to_one")


def export_city_units(cities: pd.DataFrame) -> None:
    ee.Initialize(project=EE_PROJECT)
    collection = ee.FeatureCollection(UCDB_ASSET).filter(
        ee.Filter.inList("uc_id", cities["uc_id"].tolist())
    )

    def units(feature: ee.Feature) -> ee.FeatureCollection:
        feature = ee.Feature(feature)
        city_id = feature.get("uc_id")
        core = feature.geometry().simplify(250)
        ring = core.buffer(20000).difference(core.buffer(10000), 250).simplify(250)
        return ee.FeatureCollection(
            [
                ee.Feature(core, {"uc_id": city_id, "unit": "core"}),
                ee.Feature(ring, {"uc_id": city_id, "unit": "ring"}),
            ]
        )

    info = collection.map(units).flatten().getInfo()
    geojson = {"type": "FeatureCollection", "features": info["features"]}
    with (OUT / "goes_city_units.geojson").open("w", encoding="utf-8") as stream:
        json.dump(geojson, stream, separators=(",", ":"))


def main() -> None:
    cities = select_cities()
    intervals = pd.read_csv(PILOT_INTERVALS)
    events = load_city_events(cities, intervals)
    cities.to_csv(OUT / "goes_sunset_pilot_cities.csv", index=False)
    intervals.to_csv(OUT / "goes_sunset_pilot_intervals.csv", index=False)
    events.to_csv(OUT / "goes_sunset_city_events.csv", index=False)
    export_city_units(cities)
    print("held-out cities", len(cities))
    print("city-events with hydroclimate data", len(events))
    print("severe-hot city-events", int(events["severe_hot"].sum()))
    print("lower-severity-hot city-events", int(events["lower_severity_hot"].sum()))


if __name__ == "__main__":
    main()
