from __future__ import annotations

import io
import hashlib
import json
from pathlib import Path
import time

import h5py
import numpy as np
import pandas as pd
import requests

from run_goes_event_aware_inference import exact_wild_interval_test, fit_twfe


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/grl_deepening_2026/multiplatform_replication_audit"

PAIR_DEFINITIONS = [
    {
        "name": "historical_goes18_minus_goes16",
        "sensor_a": "GOES18",
        "sensor_b": "GOES16",
        "hourly_a": ROOT
        / "outputs/goes18_2022_2024_same_sensor/goes_sunset_hourly_analysis.parquet",
        "hourly_b": ROOT
        / "outputs/goes16_2018_2024_full_census/goes_sunset_hourly_analysis.parquet",
        "metrics_a": ROOT
        / "outputs/goes18_2022_2024_same_sensor/goes_sunset_city_event_metrics.parquet",
        "metrics_b": ROOT
        / "outputs/goes16_2018_2024_full_census/goes_sunset_city_event_metrics.parquet",
        "cities": ROOT
        / "data/goes18_2022_2024_same_sensor/goes18_2022_2024_cities.csv",
        "bucket_a": "noaa-goes18",
        "bucket_b": "noaa-goes16",
        "period": "historical_2022_2024",
    },
    {
        "name": "holdout_goes18_minus_goes19",
        "sensor_a": "GOES18",
        "sensor_b": "GOES19",
        "hourly_a": ROOT
        / "outputs/goes18_2025_western_replication/goes_sunset_hourly_analysis.parquet",
        "hourly_b": ROOT
        / "outputs/goes19_2025_holdout/goes_sunset_hourly_analysis.parquet",
        "metrics_a": ROOT
        / "outputs/goes18_2025_western_replication/goes_sunset_city_event_metrics.parquet",
        "metrics_b": ROOT
        / "outputs/goes19_2025_holdout/goes_sunset_city_event_metrics.parquet",
        "cities": ROOT
        / "data/goes18_2025_western_replication/goes18_2025_cities.csv",
        "bucket_a": "noaa-goes18",
        "bucket_b": "noaa-goes19",
        "period": "holdout_2025",
    },
]

PAIR_KEYS = [
    "uc_id",
    "event_year",
    "event_step8",
    "event_time_id",
    "local_date",
    "target_hour_from_sunset",
]


def scalar(dataset: h5py.Dataset) -> float:
    value = dataset[()]
    return float(np.asarray(value).reshape(-1)[0])


def source_metadata(bucket: str, source_key: str) -> dict[str, object]:
    url = f"https://{bucket}.s3.amazonaws.com/{source_key}"
    cache_dir = OUT / "projection_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_name = hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json"
    cache_path = cache_dir / cache_name
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    response = None
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            break
        except requests.RequestException as error:
            last_error = error
            if attempt == 5:
                raise
            time.sleep(2**attempt)
    if response is None:
        raise RuntimeError(f"Metadata request failed: {url}") from last_error
    with h5py.File(io.BytesIO(response.content), "r") as handle:
        projection = handle["goes_imager_projection"]
        longitude = (
            scalar(handle["nominal_satellite_subpoint_lon"])
            if "nominal_satellite_subpoint_lon" in handle
            else float(projection.attrs["longitude_of_projection_origin"][0])
        )
        latitude = (
            scalar(handle["nominal_satellite_subpoint_lat"])
            if "nominal_satellite_subpoint_lat" in handle
            else float(projection.attrs["latitude_of_projection_origin"][0])
        )
        height_km = (
            scalar(handle["nominal_satellite_height"])
            if "nominal_satellite_height" in handle
            else float(projection.attrs["perspective_point_height"][0]) / 1000
        )
    result = {
        "source_key": source_key,
        "source_url": url,
        "nominal_subpoint_lon": longitude,
        "nominal_subpoint_lat": latitude,
        "nominal_height_km": height_km,
    }
    cache_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def view_zenith_angle(
    latitude: pd.Series,
    longitude: pd.Series,
    subpoint_latitude: pd.Series,
    subpoint_longitude: pd.Series,
    height_km: pd.Series,
) -> np.ndarray:
    lat = np.deg2rad(latitude.to_numpy(dtype=float))
    lon = np.deg2rad(longitude.to_numpy(dtype=float))
    sub_lat = np.deg2rad(subpoint_latitude.to_numpy(dtype=float))
    sub_lon = np.deg2rad(subpoint_longitude.to_numpy(dtype=float))
    cos_psi = (
        np.sin(lat) * np.sin(sub_lat)
        + np.cos(lat) * np.cos(sub_lat) * np.cos(lon - sub_lon)
    )
    earth_radius = 6378.137
    satellite_radius = earth_radius + height_km.to_numpy(dtype=float)
    distance = np.sqrt(
        satellite_radius**2
        + earth_radius**2
        - 2 * satellite_radius * earth_radius * cos_psi
    )
    cos_vza = (satellite_radius * cos_psi - earth_radius) / distance
    return np.rad2deg(np.arccos(np.clip(cos_vza, -1, 1)))


def load_hourly(path: Path, sensor: str) -> pd.DataFrame:
    columns = [
        *PAIR_KEYS,
        "scan_time_utc",
        "actual_hour_from_sunset",
        "source_key",
        "core_lst_k",
        "ring_lst_k",
        "valid",
        "core_ring_anomaly_k",
        "hydroclimatic_severity",
        "t2m_true_night_pct_rank",
        "true_night_heat",
        "severe_hot",
        "lower_severity_hot",
        "qa",
    ]
    frame = pd.read_parquet(path, columns=columns)
    frame = frame[frame["qa"].eq("recommended")].copy()
    frame["uc_id"] = frame["uc_id"].astype(str)
    rename = {
        column: f"{column}_{sensor}"
        for column in frame.columns
        if column not in PAIR_KEYS
    }
    return frame.rename(columns=rename)


def projection_table(
    frame: pd.DataFrame,
    sensor: str,
    bucket: str,
) -> pd.DataFrame:
    key_column = f"source_key_{sensor}"
    representatives = (
        frame[["event_time_id", key_column]]
        .dropna()
        .drop_duplicates()
        .sort_values(["event_time_id", key_column])
        .groupby("event_time_id", as_index=False)
        .first()
    )
    rows = []
    for row in representatives.itertuples(index=False):
        metadata = source_metadata(bucket, getattr(row, key_column))
        rows.append(
            {
                "event_time_id": row.event_time_id,
                "sensor": sensor,
                **metadata,
            }
        )
    return pd.DataFrame(rows)


def exact_hourly_pair(definition: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    sensor_a = str(definition["sensor_a"])
    sensor_b = str(definition["sensor_b"])
    hourly_a = load_hourly(Path(definition["hourly_a"]), sensor_a)
    hourly_b = load_hourly(Path(definition["hourly_b"]), sensor_b)
    metadata_a = projection_table(hourly_a, sensor_a, str(definition["bucket_a"]))
    metadata_b = projection_table(hourly_b, sensor_b, str(definition["bucket_b"]))
    metadata = pd.concat([metadata_a, metadata_b], ignore_index=True)

    paired = hourly_a.merge(
        hourly_b,
        on=PAIR_KEYS,
        how="inner",
        validate="one_to_one",
    )
    scan_a = pd.to_datetime(
        paired[f"scan_time_utc_{sensor_a}"], utc=True, format="mixed"
    )
    scan_b = pd.to_datetime(
        paired[f"scan_time_utc_{sensor_b}"], utc=True, format="mixed"
    )
    paired["scan_offset_min"] = (scan_a - scan_b).dt.total_seconds().abs() / 60
    paired["paired_valid"] = (
        paired[f"valid_{sensor_a}"].astype(bool)
        & paired[f"valid_{sensor_b}"].astype(bool)
        & paired["scan_offset_min"].le(15)
    )
    paired["true_night_heat"] = paired[
        f"true_night_heat_{sensor_a}"
    ].astype(bool)
    paired["hydroclimatic_severity"] = paired[
        f"hydroclimatic_severity_{sensor_a}"
    ]
    paired["t2m_true_night_pct_rank"] = paired[
        f"t2m_true_night_pct_rank_{sensor_a}"
    ]
    return paired, metadata


def city_event_transition(
    paired: pd.DataFrame,
    metadata: pd.DataFrame,
    cities_path: Path,
    sensor_a: str,
    sensor_b: str,
    period: str,
) -> pd.DataFrame:
    frame = paired[paired["paired_valid"] & paired["true_night_heat"]].copy()
    frame["period_window"] = np.select(
        [
            frame["target_hour_from_sunset"].between(-3, -1),
            frame["target_hour_from_sunset"].between(4, 6),
        ],
        ["pre", "late"],
        default="other",
    )
    frame = frame[frame["period_window"].isin(["pre", "late"])]
    for sensor in [sensor_a, sensor_b]:
        frame[f"mean_surface_k_{sensor}"] = (
            frame[f"core_lst_k_{sensor}"] + frame[f"ring_lst_k_{sensor}"]
        ) / 2
    daily_keys = [
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "local_date",
        "period_window",
    ]
    daily = (
        frame.groupby(daily_keys, observed=True)
        .agg(
            **{
                f"anomaly_{sensor_a}": (
                    f"core_ring_anomaly_k_{sensor_a}",
                    "mean",
                ),
                f"anomaly_{sensor_b}": (
                    f"core_ring_anomaly_k_{sensor_b}",
                    "mean",
                ),
                f"mean_surface_{sensor_a}": (
                    f"mean_surface_k_{sensor_a}",
                    "mean",
                ),
                f"mean_surface_{sensor_b}": (
                    f"mean_surface_k_{sensor_b}",
                    "mean",
                ),
            },
            scan_offset_min=("scan_offset_min", "mean"),
            n_hours=("target_hour_from_sunset", "nunique"),
            hydroclimatic_severity=("hydroclimatic_severity", "first"),
            t2m_true_night_pct_rank=("t2m_true_night_pct_rank", "first"),
        )
        .reset_index()
    )
    daily = daily[daily["n_hours"].ge(2)]
    index = [
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "local_date",
    ]
    values = [
        f"anomaly_{sensor_a}",
        f"anomaly_{sensor_b}",
        f"mean_surface_{sensor_a}",
        f"mean_surface_{sensor_b}",
        "scan_offset_min",
        "hydroclimatic_severity",
        "t2m_true_night_pct_rank",
    ]
    wide = daily.pivot(index=index, columns="period_window", values=values)
    wide.columns = [f"{name}_{window}" for name, window in wide.columns]
    wide = wide.reset_index()
    required = [
        f"anomaly_{sensor_a}_pre",
        f"anomaly_{sensor_a}_late",
        f"anomaly_{sensor_b}_pre",
        f"anomaly_{sensor_b}_late",
    ]
    wide = wide.dropna(subset=required)
    for sensor in [sensor_a, sensor_b]:
        wide[f"transition_{sensor}"] = (
            wide[f"anomaly_{sensor}_late"] - wide[f"anomaly_{sensor}_pre"]
        )
    wide["transition_difference"] = (
        wide[f"transition_{sensor_a}"] - wide[f"transition_{sensor_b}"]
    )
    wide["transition_consensus"] = (
        wide[f"transition_{sensor_a}"] + wide[f"transition_{sensor_b}"]
    ) / 2
    wide["pre_surface_consensus"] = (
        wide[f"mean_surface_{sensor_a}_pre"]
        + wide[f"mean_surface_{sensor_b}_pre"]
    ) / 2
    wide["scan_offset_min"] = wide[["scan_offset_min_pre", "scan_offset_min_late"]].mean(axis=1)
    wide["hydroclimatic_severity"] = wide[
        ["hydroclimatic_severity_pre", "hydroclimatic_severity_late"]
    ].mean(axis=1)
    wide["t2m_true_night_pct_rank"] = wide[
        ["t2m_true_night_pct_rank_pre", "t2m_true_night_pct_rank_late"]
    ].mean(axis=1)

    event_keys = ["uc_id", "event_year", "event_step8", "event_time_id"]
    measures = [
        f"transition_{sensor_a}",
        f"transition_{sensor_b}",
        "transition_difference",
        "transition_consensus",
        "pre_surface_consensus",
        "scan_offset_min",
        "hydroclimatic_severity",
        "t2m_true_night_pct_rank",
    ]
    city_event = wide.groupby(event_keys, observed=True)[measures].mean().reset_index()
    counts = wide.groupby(event_keys, observed=True).size().rename("n_paired_days").reset_index()
    city_event = city_event.merge(counts, on=event_keys, validate="one_to_one")
    city_event = city_event[city_event["n_paired_days"].ge(2)].copy()
    city_event["severity10"] = city_event["hydroclimatic_severity"] / 10

    cities = pd.read_csv(cities_path, dtype={"uc_id": str})
    city_event = city_event.merge(
        cities[["uc_id", "lat", "lon"]],
        on="uc_id",
        how="left",
        validate="many_to_one",
    )
    meta_a = metadata[metadata["sensor"].eq(sensor_a)].rename(
        columns={
            "nominal_subpoint_lon": f"subpoint_lon_{sensor_a}",
            "nominal_subpoint_lat": f"subpoint_lat_{sensor_a}",
            "nominal_height_km": f"height_km_{sensor_a}",
        }
    )
    meta_b = metadata[metadata["sensor"].eq(sensor_b)].rename(
        columns={
            "nominal_subpoint_lon": f"subpoint_lon_{sensor_b}",
            "nominal_subpoint_lat": f"subpoint_lat_{sensor_b}",
            "nominal_height_km": f"height_km_{sensor_b}",
        }
    )
    city_event = city_event.merge(
        meta_a[
            [
                "event_time_id",
                f"subpoint_lon_{sensor_a}",
                f"subpoint_lat_{sensor_a}",
                f"height_km_{sensor_a}",
            ]
        ],
        on="event_time_id",
        how="left",
        validate="many_to_one",
    ).merge(
        meta_b[
            [
                "event_time_id",
                f"subpoint_lon_{sensor_b}",
                f"subpoint_lat_{sensor_b}",
                f"height_km_{sensor_b}",
            ]
        ],
        on="event_time_id",
        how="left",
        validate="many_to_one",
    )
    for sensor in [sensor_a, sensor_b]:
        city_event[f"vza_{sensor}"] = view_zenith_angle(
            city_event["lat"],
            city_event["lon"],
            city_event[f"subpoint_lat_{sensor}"],
            city_event[f"subpoint_lon_{sensor}"],
            city_event[f"height_km_{sensor}"],
        )
    city_event["vza_difference"] = (
        city_event[f"vza_{sensor_a}"] - city_event[f"vza_{sensor_b}"]
    )
    city_event["vza_difference_centered"] = (
        city_event["vza_difference"] - city_event["vza_difference"].mean()
    )
    city_event["severity_x_vza"] = (
        city_event["severity10"] * city_event["vza_difference_centered"]
    )
    for column in [
        "t2m_true_night_pct_rank",
        "pre_surface_consensus",
        "scan_offset_min",
    ]:
        city_event[f"z_{column}"] = (
            city_event[column] - city_event[column].mean()
        ) / city_event[column].std(ddof=0)
    city_event["period"] = period
    return city_event


def model_and_test(
    frame: pd.DataFrame,
    outcome: str,
    predictors: list[str],
    focal_term: str,
    name: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    model, _ = fit_twfe(frame, outcome, predictors, name)
    wild = exact_wild_interval_test(frame, outcome, predictors, focal_term)
    wild["analysis"] = name
    wild["outcome"] = outcome
    wild["focal_term"] = focal_term
    return model.assign(analysis=name), wild


def availability_panel(definition: dict[str, object]) -> pd.DataFrame:
    sensor_a = str(definition["sensor_a"])
    sensor_b = str(definition["sensor_b"])
    columns = [
        "uc_id",
        "event_time_id",
        "event_year",
        "event_step8",
        "n_transition_days",
        "hydroclimatic_severity",
        "t2m_true_night_pct_rank",
        "true_night_heat",
        "qa",
    ]
    first = pd.read_parquet(Path(definition["metrics_a"]), columns=columns)
    second = pd.read_parquet(Path(definition["metrics_b"]), columns=columns)
    first = first[first["qa"].eq("recommended") & first["true_night_heat"]].copy()
    second = second[second["qa"].eq("recommended") & second["true_night_heat"]].copy()
    keys = ["uc_id", "event_time_id", "event_year", "event_step8"]
    first["uc_id"] = first["uc_id"].astype(str)
    second["uc_id"] = second["uc_id"].astype(str)
    pair = first.merge(second, on=keys, suffixes=("_a", "_b"), how="inner")
    rows = []
    for sensor, suffix, indicator in [
        (sensor_a, "a", 1.0),
        (sensor_b, "b", 0.0),
    ]:
        part = pair[keys].copy()
        part["sensor"] = sensor
        part["sensor_indicator"] = indicator
        part["transition_available"] = pair[f"n_transition_days_{suffix}"].ge(2).astype(float)
        part["hydroclimatic_severity"] = pair[
            f"hydroclimatic_severity_{suffix}"
        ]
        part["t2m_true_night_pct_rank"] = pair[
            f"t2m_true_night_pct_rank_{suffix}"
        ]
        rows.append(part)
    panel = pd.concat(rows, ignore_index=True)
    panel["severity10"] = panel["hydroclimatic_severity"] / 10
    panel["severity_x_sensor"] = panel["severity10"] * panel["sensor_indicator"]
    panel["z_night_heat"] = (
        panel["t2m_true_night_pct_rank"]
        - panel["t2m_true_night_pct_rank"].mean()
    ) / panel["t2m_true_night_pct_rank"].std(ddof=0)
    panel["period"] = definition["period"]
    return panel


def selected_event_panel() -> pd.DataFrame:
    frame = pd.read_parquet(
        ROOT
        / "outputs/grl_deepening_2026/baseline_adjusted_transition/baseline_adjusted_panel.parquet"
    )
    frame = frame[
        frame["cohort"].eq("goes16_full_2018_2024")
        & frame["true_night_heat"].astype(bool)
    ].copy()
    intervals = pd.read_csv(
        ROOT / "data/goes16_2018_2024_full_census/goes_sunset_intervals.csv"
    )
    frame = frame.merge(
        intervals[["time_id", "previously_selected"]].rename(
            columns={"time_id": "event_time_id"}
        ),
        on="event_time_id",
        how="left",
        validate="many_to_one",
    )
    frame["selected12"] = frame["previously_selected"].astype(float)
    frame["severity_x_selected"] = frame["severity10"] * frame["selected12"]
    return frame


def agreement_summary(
    hourly: pd.DataFrame,
    city_event: pd.DataFrame,
    sensor_a: str,
    sensor_b: str,
    name: str,
) -> dict[str, object]:
    valid = hourly[hourly["paired_valid"] & hourly["true_night_heat"]].copy()
    anomaly_difference = (
        valid[f"core_ring_anomaly_k_{sensor_a}"]
        - valid[f"core_ring_anomaly_k_{sensor_b}"]
    )
    transition_difference = city_event["transition_difference"]
    return {
        "pair": name,
        "sensor_a": sensor_a,
        "sensor_b": sensor_b,
        "n_paired_hourly": int(len(valid)),
        "n_city_events": int(len(city_event)),
        "n_cities": int(city_event["uc_id"].nunique()),
        "n_intervals": int(city_event["event_time_id"].nunique()),
        "hourly_anomaly_mean_difference_k": float(anomaly_difference.mean()),
        "hourly_anomaly_mae_k": float(anomaly_difference.abs().mean()),
        "hourly_anomaly_rmse_k": float(np.sqrt(np.mean(anomaly_difference**2))),
        "transition_mean_difference_k": float(transition_difference.mean()),
        "transition_mae_k": float(transition_difference.abs().mean()),
        "transition_rmse_k": float(np.sqrt(np.mean(transition_difference**2))),
        "mean_abs_scan_offset_min": float(valid["scan_offset_min"].mean()),
        "mean_vza_difference_deg": float(city_event["vza_difference"].mean()),
        "sd_vza_difference_deg": float(city_event["vza_difference"].std()),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    model_frames: list[pd.DataFrame] = []
    wild_rows: list[dict[str, object]] = []
    metadata_frames: list[pd.DataFrame] = []
    availability_frames: list[pd.DataFrame] = []
    city_event_frames: list[pd.DataFrame] = []
    agreements: list[dict[str, object]] = []

    for definition in PAIR_DEFINITIONS:
        name = str(definition["name"])
        sensor_a = str(definition["sensor_a"])
        sensor_b = str(definition["sensor_b"])
        hourly, metadata = exact_hourly_pair(definition)
        metadata["pair"] = name
        metadata_frames.append(metadata)
        city_event = city_event_transition(
            hourly,
            metadata,
            Path(definition["cities"]),
            sensor_a,
            sensor_b,
            str(definition["period"]),
        )
        city_event["pair"] = name
        city_event_frames.append(city_event)
        agreements.append(
            agreement_summary(hourly, city_event, sensor_a, sensor_b, name)
        )

        controls = [
            "severity10",
            "z_t2m_true_night_pct_rank",
            "z_pre_surface_consensus",
            "z_scan_offset_min",
        ]
        for outcome, label in [
            (f"transition_{sensor_a}", f"{name}_{sensor_a}_slope"),
            (f"transition_{sensor_b}", f"{name}_{sensor_b}_slope"),
            ("transition_consensus", f"{name}_consensus_slope"),
            ("transition_difference", f"{name}_sensor_difference"),
        ]:
            model, _ = fit_twfe(city_event, outcome, controls, label)
            model_frames.append(model.assign(analysis=label))
        for outcome, label in [
            ("transition_consensus", f"{name}_consensus_slope"),
            ("transition_difference", f"{name}_sensor_difference"),
        ]:
            wild = exact_wild_interval_test(
                city_event, outcome, controls, "severity10"
            )
            wild.update(
                {
                    "analysis": label,
                    "outcome": outcome,
                    "focal_term": "severity10",
                }
            )
            wild_rows.append(wild)

        geometry_predictors = [*controls, "severity_x_vza"]
        geometry_model, geometry_wild = model_and_test(
            city_event,
            "transition_difference",
            geometry_predictors,
            "severity_x_vza",
            f"{name}_view_geometry",
        )
        model_frames.append(geometry_model)
        wild_rows.append(geometry_wild)

        availability = availability_panel(definition)
        availability_frames.append(availability)
        availability_model, availability_wild = model_and_test(
            availability,
            "transition_available",
            ["severity10", "sensor_indicator", "severity_x_sensor", "z_night_heat"],
            "severity_x_sensor",
            f"{name}_availability_interaction",
        )
        model_frames.append(availability_model)
        wild_rows.append(availability_wild)

    selected = selected_event_panel()
    for outcome, predictors, label in [
        (
            "transition_shift_k",
            [
                "severity10",
                "severity_x_selected",
                "t2m_true_night_c",
                "pre_mean_surface_c",
                "pre_core_ring_anomaly_k",
            ],
            "selected12_transition_inflation",
        ),
        (
            "late_core_ring_anomaly_k",
            [
                "severity10",
                "severity_x_selected",
                "t2m_true_night_c",
                "pre_mean_surface_c",
                "pre_core_ring_anomaly_k",
            ],
            "selected12_late_anomaly_inflation",
        ),
    ]:
        model, wild = model_and_test(
            selected,
            outcome,
            predictors,
            "severity_x_selected",
            label,
        )
        model_frames.append(model)
        wild_rows.append(wild)

    historical = city_event_frames[0].copy()
    holdout = city_event_frames[1].copy()
    historical["period_2025"] = 0.0
    holdout["period_2025"] = 1.0
    transfer = pd.concat([historical, holdout], ignore_index=True, sort=False)
    transfer["severity_x_2025"] = transfer["severity10"] * transfer["period_2025"]
    for column in [
        "t2m_true_night_pct_rank",
        "pre_surface_consensus",
        "scan_offset_min",
    ]:
        transfer[f"z_{column}"] = (
            transfer[column] - transfer[column].mean()
        ) / transfer[column].std(ddof=0)
    transfer_predictors = [
        "severity10",
        "severity_x_2025",
        "z_t2m_true_night_pct_rank",
        "z_pre_surface_consensus",
        "z_scan_offset_min",
    ]
    transfer_model, transfer_wild = model_and_test(
        transfer,
        "transition_consensus",
        transfer_predictors,
        "severity_x_2025",
        "consensus_temporal_transfer",
    )
    model_frames.append(transfer_model)
    wild_rows.append(transfer_wild)

    models = pd.concat(model_frames, ignore_index=True)
    wild = pd.DataFrame(wild_rows)
    metadata = pd.concat(metadata_frames, ignore_index=True)
    availability = pd.concat(availability_frames, ignore_index=True)
    city_events = pd.concat(city_event_frames, ignore_index=True, sort=False)
    agreement = pd.DataFrame(agreements)

    models.to_csv(OUT / "replication_audit_models.csv", index=False)
    wild.to_csv(OUT / "replication_audit_wild_tests.csv", index=False)
    metadata.to_csv(OUT / "projection_metadata.csv", index=False)
    availability.to_parquet(OUT / "availability_panel.parquet", index=False)
    city_events.to_parquet(OUT / "exact_paired_city_events.parquet", index=False)
    selected.to_parquet(OUT / "selected_event_panel.parquet", index=False)
    transfer.to_parquet(OUT / "consensus_transfer_panel.parquet", index=False)
    agreement.to_csv(OUT / "paired_agreement_summary.csv", index=False)

    report = {
        "protocol": str(ROOT / "multiplatform_replication_audit_protocol.md"),
        "agreements": agreements,
        "wild_tests": wild.to_dict(orient="records"),
    }
    with (OUT / "replication_audit_report.json").open("w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print(wild.to_string(index=False))
    print(agreement.to_string(index=False))


if __name__ == "__main__":
    main()
