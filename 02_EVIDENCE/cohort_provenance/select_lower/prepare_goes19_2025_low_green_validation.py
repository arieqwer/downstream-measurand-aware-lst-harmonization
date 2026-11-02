from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ee
import pandas as pd
import pyarrow.dataset as ds


ROOT = Path(__file__).resolve().parents[1]
UPGRADE = ROOT.parent / "reliability_dynamics_upgrade"
OUT = ROOT / "data/goes19_2025_low_green"

PANEL = UPGRADE / "data/valid_city_interval_panel.parquet"
COVARIATES = UPGRADE / "data/city_covariates.csv"
LOCATIONS = UPGRADE / "figure_source_data/figure_1a_city_locations.csv"
INTERVALS = ROOT / "data/goes19_2025_holdout/goes19_2025_intervals.csv"
PROTOCOL = ROOT / "GOES19_2025_LOW_GREEN_EXTERNAL_VALIDATION_PROTOCOL.md"
UCDB_ASSET = "projects/ee-zuruyuyu/assets/ucdb_uc_polygons_fixed_all"
EE_PROJECT = "ee-zuruyuyu"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_city_units(cities: pd.DataFrame, path: Path) -> None:
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
    with path.open("w", encoding="utf-8") as stream:
        json.dump(
            {"type": "FeatureCollection", "features": info["features"]},
            stream,
            separators=(",", ":"),
        )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    city = pd.read_csv(COVARIATES, dtype={"uc_id": str})
    locations = pd.read_csv(LOCATIONS, dtype={"uc_id": str})
    city = city.merge(locations[["uc_id", "lat", "lon"]], on="uc_id", how="inner")
    city = city[
        city["high_green"].eq(0)
        & city["un_sdg_reg"].eq("Northern America")
        & city["lon"].between(-125.0, -66.0)
        & city["lat"].between(24.0, 50.0)
    ].copy()
    city["mean_water_support_ratio"] = pd.NA
    city["heat_retention_score"] = pd.NA
    city["profile"] = "lower_vegetation_support"
    keep = [
        "uc_id",
        "un_sdg_reg",
        "high_green",
        "mean_ring_veg",
        "z_ring_green_support",
        "mean_water_support_ratio",
        "heat_retention_score",
        "profile",
        "lat",
        "lon",
    ]
    city = city[keep].sort_values("uc_id").reset_index(drop=True)
    if len(city) != 113:
        raise RuntimeError(f"Expected 113 lower-vegetation cities, found {len(city)}")

    intervals = pd.read_csv(INTERVALS)
    columns = [
        "uc_id",
        "year",
        "step8",
        "time_id",
        "rzsm_pct",
        "vpd_pct",
        "t2m_true_night_pct_rank",
        "t2m_true_night_c",
        "pr_sum",
    ]
    panel = ds.dataset(PANEL, format="parquet").to_table(columns=columns).to_pandas()
    panel["uc_id"] = panel["uc_id"].astype(str)
    panel = panel[
        panel["uc_id"].isin(city["uc_id"])
        & panel["year"].eq(2025)
    ].copy()
    panel["hydroclimatic_severity"] = (
        (100.0 - panel["rzsm_pct"]) + panel["vpd_pct"]
    ) / 2.0
    panel["true_night_heat"] = panel["t2m_true_night_pct_rank"].ge(90.0)
    panel["severe_hot"] = panel["true_night_heat"] & panel[
        "hydroclimatic_severity"
    ].ge(85.0)
    panel["lower_severity_hot"] = panel["true_night_heat"] & panel[
        "hydroclimatic_severity"
    ].le(50.0)
    events = panel.merge(
        intervals[["year", "step8", "time_id", "start_date", "end_date"]],
        on=["year", "step8", "time_id"],
        how="inner",
        validate="many_to_one",
    ).merge(city, on="uc_id", how="inner", validate="many_to_one")

    cities_path = OUT / "goes19_2025_cities.csv"
    intervals_path = OUT / "goes19_2025_intervals.csv"
    events_path = OUT / "goes19_2025_city_events.csv"
    geometry_path = OUT / "goes_city_units.geojson"
    city.to_csv(cities_path, index=False)
    intervals.to_csv(intervals_path, index=False)
    events.to_csv(events_path, index=False)
    export_city_units(city, geometry_path)

    manifest = {
        "frozen_before_goes19_outcome_inspection": True,
        "n_cities": len(city),
        "n_intervals": len(intervals),
        "sha256": {
            "protocol": sha256(PROTOCOL),
            "cities": sha256(cities_path),
            "intervals": sha256(intervals_path),
            "events": sha256(events_path),
            "geometry": sha256(geometry_path),
        },
    }
    with (OUT / "FROZEN_SELECTION.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
