#!/usr/bin/env python3
"""Build deterministic, source-traceable SI design and decision tables.

The script reads only frozen inputs and completed analysis outputs from the
original research workspace.  It never modifies that workspace.  All derived
tables are written to ``02_EVIDENCE/si_tables`` and byte-for-byte copies of the
relevant frozen manifests are written to ``04_PROTOCOLS/frozen_inputs``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


MANUSCRIPT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = MANUSCRIPT_ROOT.parent / "thermal_hysteresis_research"
DEFAULT_NAME_LOOKUP = MANUSCRIPT_ROOT.parent.parent / "ucdb_city_lookup_for_event_anatomy.csv"
DEFAULT_OUTPUT_DIR = MANUSCRIPT_ROOT / "02_EVIDENCE/si_tables"
DEFAULT_FROZEN_INPUT_DIR = MANUSCRIPT_ROOT / "04_PROTOCOLS/frozen_inputs"

MIN_CORE_PIXELS = 3
MIN_RING_PIXELS = 10
PRE_HOURS = {-3, -2, -1}
LATE_HOURS = {4, 5, 6}


@dataclass(frozen=True)
class Source:
    source_id: str
    root_label: str
    path: Path
    logical_path: str
    role: str


@dataclass(frozen=True)
class Stage:
    stage_id: str
    analysis_role: str
    reference_platform: str
    source_platform: str
    candidate_count: int
    interval_count: int
    hourly_path: str | None
    transition_path: str | None = None
    external_report_key: str | None = None


STAGES = (
    Stage(
        "initial_model_derivation_original_2022_2024",
        "model_derivation",
        "GOES18",
        "GOES16",
        51,
        31,
        "outputs/grl_deepening_2026/multiplatform_harmonization/derivation_city_event_hourly.parquet",
    ),
    Stage(
        "initial_model_evaluation_expansion_2022_2024",
        "spatial_transfer_evaluation",
        "GOES18",
        "GOES16",
        43,
        31,
        "outputs/grl_deepening_2026/multiplatform_expanded_validation/historical_expanded_predictions.parquet",
    ),
    Stage(
        "initial_model_evaluation_original_2025",
        "temporal_sensor_evaluation",
        "GOES18",
        "GOES19",
        51,
        10,
        "outputs/grl_deepening_2026/multiplatform_harmonization/validation_2025_predictions.parquet",
    ),
    Stage(
        "initial_model_evaluation_expansion_2025",
        "spatiotemporal_sensor_evaluation",
        "GOES18",
        "GOES19",
        43,
        10,
        "outputs/grl_deepening_2026/multiplatform_expanded_validation/validation_expanded_predictions.parquet",
    ),
    Stage(
        "metric_aware_calibration_combined_2025",
        "metric_specific_model_calibration",
        "GOES18",
        "GOES19",
        94,
        10,
        "outputs/grl_deepening_2026/multiplatform_expanded_validation/combined_2025_common_domain_predictions.parquet",
    ),
    Stage(
        "metric_aware_validation_combined_2026",
        "prospective_temporal_holdout",
        "GOES18",
        "GOES19",
        94,
        8,
        "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/validation_2026_hourly_predictions.parquet",
        "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/validation_2026_transition_predictions.parquet",
    ),
    Stage(
        "external_calibration_combined_2019_2020",
        "external_hour_offset_calibration",
        "GOES17",
        "GOES16",
        75,
        4,
        None,
        external_report_key="calibration",
    ),
    Stage(
        "external_validation_combined_2021",
        "external_platform_replication",
        "GOES17",
        "GOES16",
        75,
        4,
        "outputs/grl_deepening_2026/goes17_goes16_external_metric/validation_2021_hourly_predictions.parquet",
        "outputs/grl_deepening_2026/goes17_goes16_external_metric/validation_2021_transition_predictions.parquet",
        external_report_key="validation",
    ),
)


FROZEN_COPIES = {
    "GOES18_2022_2024_ORIGINAL_FROZEN_SELECTION.json": (
        "data/goes18_2022_2024_same_sensor/FROZEN_SELECTION.json"
    ),
    "GOES18_2022_2024_EXPANSION_FROZEN_SELECTION.json": (
        "data/goes18_2022_2024_expansion/FROZEN_SELECTION.json"
    ),
    "GOES18_2025_ORIGINAL_FROZEN_SELECTION.json": (
        "data/goes18_2025_western_replication/FROZEN_SELECTION.json"
    ),
    "GOES18_2025_EXPANSION_FROZEN_SELECTION.json": (
        "data/goes18_2025_expansion/FROZEN_SELECTION.json"
    ),
    "GOES18_2026_FROZEN_SELECTION.json": (
        "data/goes18_2026_metric_holdout/FROZEN_SELECTION.json"
    ),
    "GOES19_2026_FROZEN_SELECTION.json": (
        "data/goes19_2026_metric_holdout/FROZEN_SELECTION.json"
    ),
    "INITIAL_HARMONIZATION_FROZEN_MANIFEST.json": (
        "outputs/grl_deepening_2026/multiplatform_harmonization/frozen_harmonization_manifest.json"
    ),
    "METRIC_AWARE_HARMONIZATION_FROZEN_MANIFEST.json": (
        "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/frozen_metric_aware_manifest.json"
    ),
}


EXPECTED_STAGE_COUNTS = {
    "initial_model_derivation_original_2022_2024": (44, 13_454, 1_352),
    "initial_model_evaluation_expansion_2022_2024": (31, 9_197, 886),
    "initial_model_evaluation_original_2025": (44, 4_180, 435),
    "initial_model_evaluation_expansion_2025": (31, 2_963, 298),
    "metric_aware_calibration_combined_2025": (75, 7_143, 733),
    "metric_aware_validation_combined_2026": (75, 5_744, 588),
    "external_calibration_combined_2019_2020": (69, 2_533, None),
    "external_validation_combined_2021": (69, 2_571, 246),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"uc_id": "string"})


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(
        path,
        index=False,
        lineterminator="\n",
        float_format="%.15g",
        na_rep="",
    )


def city_ids(frame: pd.DataFrame) -> set[str]:
    return set(frame["uc_id"].astype("string"))


def prediction_ids(source_root: Path, relative_path: str) -> set[str]:
    frame = pd.read_parquet(source_root / relative_path, columns=["uc_id"])
    return set(frame["uc_id"].astype("string"))


def external_calibration_ids(source_root: Path) -> set[str]:
    """Reproduce the frozen external pairing filter only far enough to recover IDs."""
    pair_keys = [
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "local_date",
        "target_hour_from_sunset",
    ]

    def sensor(path: Path, name: str) -> pd.DataFrame:
        columns = [
            *pair_keys,
            "scan_time_utc",
            "core_recommended_count",
            "ring_recommended_count",
            "core_recommended_lst_k",
            "ring_recommended_lst_k",
        ]
        frame = pd.read_parquet(path, columns=columns)
        frame["uc_id"] = frame["uc_id"].astype("string")
        frame[f"valid_{name}"] = (
            frame["core_recommended_count"].ge(MIN_CORE_PIXELS)
            & frame["ring_recommended_count"].ge(MIN_RING_PIXELS)
            & frame["core_recommended_lst_k"].between(180, 380)
            & frame["ring_recommended_lst_k"].between(180, 380)
        )
        return frame[[*pair_keys, "scan_time_utc", f"valid_{name}"]].rename(
            columns={"scan_time_utc": f"scan_time_utc_{name}"}
        )

    target = sensor(
        source_root / "data/goes17_2019_2021_external_metric/goes_sunset_hourly.parquet",
        "GOES17",
    )
    source = sensor(
        source_root / "data/goes16_2019_2021_external_metric/goes_sunset_hourly.parquet",
        "GOES16",
    )
    paired = target.merge(source, on=pair_keys, how="inner", validate="one_to_one")
    scan_target = pd.to_datetime(paired["scan_time_utc_GOES17"], utc=True, format="mixed")
    scan_source = pd.to_datetime(paired["scan_time_utc_GOES16"], utc=True, format="mixed")
    paired_valid = (
        paired["valid_GOES17"]
        & paired["valid_GOES16"]
        & (scan_target - scan_source).dt.total_seconds().abs().div(60).le(15)
    )
    retained = (
        paired.loc[paired_valid & paired["event_year"].le(2020)]
        .groupby(
            [
                "uc_id",
                "event_year",
                "event_step8",
                "event_time_id",
                "target_hour_from_sunset",
            ],
            observed=True,
        )["local_date"]
        .nunique()
    )
    ids = set(retained[retained.ge(2)].reset_index()["uc_id"].astype("string"))
    require(len(ids) == 69, "External calibration membership should contain 69 cities")
    return ids


def mask_wide(path: Path, prefix: str) -> pd.DataFrame:
    frame = read_csv(path)
    wide = frame.pivot(index="uc_id", columns="unit", values="n_grid_pixels")
    require({"core", "ring"}.issubset(wide.columns), f"Missing core/ring mask units: {path}")
    wide = wide[["core", "ring"]].rename(
        columns={
            "core": f"{prefix}_core_grid_pixels",
            "ring": f"{prefix}_ring_grid_pixels",
        }
    )
    wide[f"{prefix}_grid_eligible"] = (
        wide[f"{prefix}_core_grid_pixels"].ge(MIN_CORE_PIXELS)
        & wide[f"{prefix}_ring_grid_pixels"].ge(MIN_RING_PIXELS)
    )
    return wide.reset_index()


def build_city_metadata(source_root: Path, name_lookup: Path) -> pd.DataFrame:
    fixed = read_csv(source_root / "data/goes18_2026_metric_holdout/goes_sunset_cities.csv")
    original = read_csv(source_root / "data/goes18_2022_2024_same_sensor/goes_sunset_cities.csv")
    expansion = read_csv(source_root / "data/goes18_2022_2024_expansion/goes_sunset_cities.csv")
    external = read_csv(source_root / "data/goes16_2019_2021_external_metric/goes_sunset_cities.csv")

    require(len(fixed) == fixed["uc_id"].nunique() == 94, "Fixed combined candidate list is not 94 unique cities")
    require(len(original) == original["uc_id"].nunique() == 51, "Original candidate list is not 51 unique cities")
    require(len(expansion) == expansion["uc_id"].nunique() == 43, "Expansion candidate list is not 43 unique cities")
    require(city_ids(original).isdisjoint(city_ids(expansion)), "Original and expansion candidates overlap")
    require(city_ids(original) | city_ids(expansion) == city_ids(fixed), "The 51+43 candidate union does not equal the frozen 94-city list")
    require(len(external) == external["uc_id"].nunique() == 75, "External candidate list is not 75 unique cities")

    lookup = read_csv(name_lookup)[["uc_id", "uc_name", "lat", "lon", "region"]]
    require(not lookup["uc_id"].duplicated().any(), "City-name lookup has duplicate uc_id values")
    lookup = lookup.rename(
        columns={
            "lat": "lookup_lat",
            "lon": "lookup_lon",
            "region": "lookup_region",
        }
    )
    fixed = fixed.merge(lookup, on="uc_id", how="left", validate="one_to_one")
    require(fixed["uc_name"].notna().all(), "At least one frozen city lacks a name")
    require(
        np.allclose(fixed["lat"], fixed["lookup_lat"], atol=1e-9, rtol=0)
        and np.allclose(fixed["lon"], fixed["lookup_lon"], atol=1e-9, rtol=0),
        "Candidate and auxiliary lookup coordinates disagree",
    )

    for prefix, relative_path in (
        ("goes18_2026", "data/goes18_2026_metric_holdout/goes_city_grid_mask_summary.csv"),
        ("goes19_2026", "data/goes19_2026_metric_holdout/goes_city_grid_mask_summary.csv"),
    ):
        fixed = fixed.merge(
            mask_wide(source_root / relative_path, prefix),
            on="uc_id",
            how="left",
            validate="one_to_one",
        )
    fixed["paired_2026_grid_eligible"] = (
        fixed["goes18_2026_grid_eligible"] & fixed["goes19_2026_grid_eligible"]
    )

    original_ids = city_ids(original)
    expansion_ids = city_ids(expansion)
    external_ids = city_ids(external)
    fixed["candidate_2022_2024_original"] = fixed["uc_id"].isin(original_ids)
    fixed["candidate_2022_2024_expansion"] = fixed["uc_id"].isin(expansion_ids)
    fixed["candidate_2025_original"] = fixed["uc_id"].isin(original_ids)
    fixed["candidate_2025_expansion"] = fixed["uc_id"].isin(expansion_ids)
    fixed["candidate_2025_combined"] = True
    fixed["candidate_2026_combined"] = True
    fixed["candidate_external_2019_2021"] = fixed["uc_id"].isin(external_ids)

    analysis_memberships = {
        "analyzed_derivation_2022_2024_original": STAGES[0].hourly_path,
        "analyzed_evaluation_2022_2024_expansion": STAGES[1].hourly_path,
        "analyzed_evaluation_2025_original": STAGES[2].hourly_path,
        "analyzed_evaluation_2025_expansion": STAGES[3].hourly_path,
        "analyzed_calibration_2025_combined": STAGES[4].hourly_path,
        "analyzed_holdout_2026_combined": STAGES[5].hourly_path,
        "analyzed_external_validation_2021": STAGES[7].hourly_path,
    }
    for column, relative_path in analysis_memberships.items():
        require(relative_path is not None, f"Missing prediction path for {column}")
        fixed[column] = fixed["uc_id"].isin(prediction_ids(source_root, relative_path))
    fixed["analyzed_external_calibration_2019_2020"] = fixed["uc_id"].isin(
        external_calibration_ids(source_root)
    )

    require(int(fixed["goes18_2026_grid_eligible"].sum()) == 88, "Unexpected GOES-18 eligible-grid count")
    require(int(fixed["goes19_2026_grid_eligible"].sum()) == 83, "Unexpected GOES-19 eligible-grid count")
    require(int(fixed["paired_2026_grid_eligible"].sum()) == 78, "Unexpected joint 2026 eligible-grid count")

    columns = [
        "uc_id",
        "uc_name",
        "lat",
        "lon",
        "lookup_region",
        "calibration_cohort",
        "profile",
        "un_sdg_reg",
        "water_tertile",
        "storage_quartile",
        "mean_water_support_ratio",
        "heat_retention_score",
        "high_green",
        "mean_ring_veg",
        "z_ring_green_support",
        "goes18_2026_core_grid_pixels",
        "goes18_2026_ring_grid_pixels",
        "goes18_2026_grid_eligible",
        "goes19_2026_core_grid_pixels",
        "goes19_2026_ring_grid_pixels",
        "goes19_2026_grid_eligible",
        "paired_2026_grid_eligible",
        "candidate_2022_2024_original",
        "candidate_2022_2024_expansion",
        "candidate_2025_original",
        "candidate_2025_expansion",
        "candidate_2025_combined",
        "candidate_2026_combined",
        "candidate_external_2019_2021",
        *analysis_memberships.keys(),
        "analyzed_external_calibration_2019_2020",
    ]
    fixed["uc_id_sort"] = pd.to_numeric(fixed["uc_id"])
    return fixed.sort_values("uc_id_sort")[columns].reset_index(drop=True)


def canonical_intervals(
    source_root: Path,
    relative_path: str,
    design_id: str,
    reference_platform: str,
    source_platform: str,
    analysis_role: str,
    protocol: str,
) -> pd.DataFrame:
    frame = pd.read_csv(source_root / relative_path)
    frame = frame.rename(columns={"time_id": "event_time_id"})
    if "end_date" not in frame:
        frame["end_date"] = (
            pd.to_datetime(frame["start_date"], format="%Y-%m-%d") + pd.Timedelta(days=7)
        ).dt.strftime("%Y-%m-%d")
    if "analysis_role" in frame:
        row_role = frame["analysis_role"].astype(str)
    else:
        row_role = pd.Series(analysis_role, index=frame.index)
    result = pd.DataFrame(
        {
            "design_id": design_id,
            "reference_platform": reference_platform,
            "source_platform": source_platform,
            "analysis_role": row_role,
            "year": frame["year"].astype(int),
            "step8": frame["step8"].astype(int),
            "event_time_id": frame["event_time_id"].astype(int),
            "start_date": frame["start_date"].astype(str),
            "end_date": frame["end_date"].astype(str),
            "interval_days_inclusive": 8,
            "protocol": protocol,
            "frozen_status": "frozen_before_design-specific_outcome_extraction",
        }
    )
    observed_days = (
        pd.to_datetime(result["end_date"]) - pd.to_datetime(result["start_date"])
    ).dt.days + 1
    require((observed_days == 8).all(), f"Non-eight-day interval in {relative_path}")
    return result


def build_interval_chronology(source_root: Path) -> pd.DataFrame:
    frames = [
        canonical_intervals(
            source_root,
            "data/goes18_2022_2024_same_sensor/goes18_2022_2024_intervals.csv",
            "goes18_goes16_2022_2024",
            "GOES18",
            "GOES16",
            "model_derivation_original_and_spatial_evaluation_expansion",
            "MULTIPLATFORM_HARMONIZATION_PROTOCOL.md; MULTIPLATFORM_EXPANDED_VALIDATION_PROTOCOL.md",
        ),
        canonical_intervals(
            source_root,
            "data/goes19_2025_holdout/goes19_2025_intervals.csv",
            "goes18_goes19_2025",
            "GOES18",
            "GOES19",
            "initial_model_evaluation_and_metric_aware_calibration",
            "GOES19_2025_TEMPORAL_SENSOR_HOLDOUT_PROTOCOL.md; GOES18_GOES19_METRIC_AWARE_HARMONIZATION_PROTOCOL.md",
        ),
        canonical_intervals(
            source_root,
            "data/goes18_2026_metric_holdout/goes_sunset_intervals.csv",
            "goes18_goes19_2026",
            "GOES18",
            "GOES19",
            "prospective_temporal_holdout",
            "GOES18_GOES19_METRIC_AWARE_HARMONIZATION_PROTOCOL.md",
        ),
        canonical_intervals(
            source_root,
            "data/goes17_2019_2021_external_metric/goes_sunset_intervals.csv",
            "goes17_goes16_2019_2021",
            "GOES17",
            "GOES16",
            "external_calibration_or_validation",
            "GOES17_GOES16_EXTERNAL_METRIC_REPLICATION_PROTOCOL.md",
        ),
    ]
    result = pd.concat(frames, ignore_index=True)
    require(len(result) == 57, "Interval chronology should contain 57 rows")
    require(not result[["design_id", "event_time_id"]].duplicated().any(), "Duplicate design/event interval")
    return result.sort_values(["start_date", "design_id", "event_time_id"]).reset_index(drop=True)


def transition_count_from_hourly(frame: pd.DataFrame) -> int:
    keys = ["uc_id", "event_time_id"]
    presence = (
        frame.assign(
            is_pre=frame["target_hour_from_sunset"].isin(PRE_HOURS),
            is_late=frame["target_hour_from_sunset"].isin(LATE_HOURS),
        )
        .groupby(keys, observed=True)
        .agg(
            n_pre=("is_pre", "sum"),
            n_late=("is_late", "sum"),
        )
    )
    return int((presence["n_pre"].ge(2) & presence["n_late"].ge(2)).sum())


def build_attrition_summary(source_root: Path) -> pd.DataFrame:
    external_report_path = source_root / "outputs/grl_deepening_2026/goes17_goes16_external_metric/external_replication_report.json"
    external_report = json.loads(external_report_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for stage in STAGES:
        if stage.hourly_path is not None:
            hourly = pd.read_parquet(source_root / stage.hourly_path)
            analyzed_cities = int(hourly["uc_id"].nunique())
            hourly_rows = int(len(hourly))
            observed_intervals = int(hourly["event_time_id"].nunique())
            transition_rows = (
                int(len(pd.read_parquet(source_root / stage.transition_path)))
                if stage.transition_path is not None
                else transition_count_from_hourly(hourly)
            )
        else:
            require(stage.external_report_key is not None, f"No count source for {stage.stage_id}")
            report = external_report[stage.external_report_key]
            analyzed_cities = int(report["n_cities"])
            hourly_rows = int(report.get("n_rows", report.get("n_hourly")))
            observed_intervals = int(report["n_events"])
            transition_rows = report.get("n_transitions")
            transition_rows = int(transition_rows) if transition_rows is not None else None
        require(observed_intervals == stage.interval_count, f"Unexpected interval count for {stage.stage_id}")
        expected = EXPECTED_STAGE_COUNTS[stage.stage_id]
        require((analyzed_cities, hourly_rows, transition_rows) == expected, f"Unexpected analysis counts for {stage.stage_id}")
        rows.append(
            {
                "stage_id": stage.stage_id,
                "analysis_role": stage.analysis_role,
                "reference_platform": stage.reference_platform,
                "source_platform": stage.source_platform,
                "candidate_cities": stage.candidate_count,
                "analyzed_cities": analyzed_cities,
                "excluded_cities": stage.candidate_count - analyzed_cities,
                "city_retention_fraction": analyzed_cities / stage.candidate_count,
                "fixed_intervals": stage.interval_count,
                "hourly_city_event_rows": hourly_rows,
                "eligible_transition_city_events": transition_rows,
            }
        )
    return pd.DataFrame(rows)


def build_event_counts(source_root: Path, chronology: pd.DataFrame) -> pd.DataFrame:
    interval_lookup = chronology.set_index(["design_id", "event_time_id"])[["start_date", "end_date"]]
    design_for_stage = {
        "initial_model_derivation_original_2022_2024": "goes18_goes16_2022_2024",
        "initial_model_evaluation_expansion_2022_2024": "goes18_goes16_2022_2024",
        "initial_model_evaluation_original_2025": "goes18_goes19_2025",
        "initial_model_evaluation_expansion_2025": "goes18_goes19_2025",
        "metric_aware_calibration_combined_2025": "goes18_goes19_2025",
        "metric_aware_validation_combined_2026": "goes18_goes19_2026",
        "external_validation_combined_2021": "goes17_goes16_2019_2021",
    }
    rows: list[dict[str, Any]] = []
    for stage in STAGES:
        if stage.hourly_path is None:
            continue
        hourly = pd.read_parquet(source_root / stage.hourly_path)
        transition_counts: dict[int, int]
        if stage.transition_path is not None:
            transitions = pd.read_parquet(source_root / stage.transition_path)
            transition_counts = transitions.groupby("event_time_id").size().astype(int).to_dict()
        else:
            flags = hourly.assign(
                is_pre=hourly["target_hour_from_sunset"].isin(PRE_HOURS),
                is_late=hourly["target_hour_from_sunset"].isin(LATE_HOURS),
            )
            eligible = (
                flags.groupby(["event_time_id", "uc_id"], observed=True)
                .agg(n_pre=("is_pre", "sum"), n_late=("is_late", "sum"))
                .reset_index()
            )
            transition_counts = (
                eligible[eligible["n_pre"].ge(2) & eligible["n_late"].ge(2)]
                .groupby("event_time_id")
                .size()
                .astype(int)
                .to_dict()
            )
        design_id = design_for_stage[stage.stage_id]
        for event_id, event in hourly.groupby("event_time_id", observed=True, sort=True):
            event_id = int(event_id)
            dates = interval_lookup.loc[(design_id, event_id)]
            rows.append(
                {
                    "stage_id": stage.stage_id,
                    "analysis_role": stage.analysis_role,
                    "reference_platform": stage.reference_platform,
                    "source_platform": stage.source_platform,
                    "event_time_id": event_id,
                    "event_year": int(event["event_year"].iloc[0]),
                    "event_step8": int(event["event_step8"].iloc[0]),
                    "start_date": dates["start_date"],
                    "end_date": dates["end_date"],
                    "fixed_candidate_cities": stage.candidate_count,
                    "analyzed_cities_with_hourly_rows": int(event["uc_id"].nunique()),
                    "hourly_city_event_rows": int(len(event)),
                    "eligible_transition_city_events": int(transition_counts.get(event_id, 0)),
                }
            )

    external_attrition = pd.read_csv(
        source_root / "outputs/grl_deepening_2026/goes17_goes16_external_metric/event_attrition.csv"
    )
    ext_dates = chronology[chronology["design_id"].eq("goes17_goes16_2019_2021")].set_index("event_time_id")
    for _, event in external_attrition[external_attrition["analysis_role"].eq("calibration")].iterrows():
        event_id = int(event["event_time_id"])
        dates = ext_dates.loc[event_id]
        rows.append(
            {
                "stage_id": "external_calibration_combined_2019_2020",
                "analysis_role": "external_hour_offset_calibration",
                "reference_platform": "GOES17",
                "source_platform": "GOES16",
                "event_time_id": event_id,
                "event_year": int(event["event_year"]),
                "event_step8": event_id - 3000,
                "start_date": dates["start_date"],
                "end_date": dates["end_date"],
                "fixed_candidate_cities": 75,
                "analyzed_cities_with_hourly_rows": int(event["retained_cities"]),
                "hourly_city_event_rows": int(event["retained_city_event_hour_rows"]),
                "eligible_transition_city_events": None,
            }
        )
    result = pd.DataFrame(rows).sort_values(["stage_id", "event_time_id"]).reset_index(drop=True)
    require(result["hourly_city_event_rows"].sum() == 47_785, "Per-event hourly totals do not close")
    return result


def build_model_selection(source_root: Path) -> pd.DataFrame:
    initial = pd.read_csv(
        source_root / "outputs/grl_deepening_2026/multiplatform_harmonization/derivation_model_selection.csv"
    ).rename(
        columns={
            "mean_composite": "mean_cv_score",
            "sd_composite": "sd_cv_score",
            "se_composite": "se_cv_score",
        }
    )
    initial.insert(0, "selection_stage", "initial_harmonization_2022_2024")
    initial.insert(1, "outcome", "hourly_composite")
    initial["score_name"] = "mean_normalized_six_outcome_rmse_ratio"
    initial["selection_rule"] = "one_standard_error_with_predeclared_parsimony_order"
    initial["parsimony_rank"] = initial["model"].map(
        {"raw": 1, "hour_offset": 2, "hour_spline": 3, "geometry_ridge": 4}
    )

    metric = pd.read_csv(
        source_root / "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/model_selection.csv"
    ).rename(
        columns={
            "mean_rmse_ratio": "mean_cv_score",
            "sd_rmse_ratio": "sd_cv_score",
            "se_rmse_ratio": "se_cv_score",
        }
    )
    metric.insert(0, "selection_stage", "metric_aware_calibration_2025")
    metric["score_name"] = "rmse_ratio_to_raw"
    metric["selection_rule"] = "one_standard_error_with_predeclared_parsimony_order"
    hourly_rank = {"raw": 1, "hour_offset": 2, "geometry_ridge": 3, "scene_gbdt": 4}
    transition_rank = {"raw": 1, "mean_offset": 2, "transition_ridge": 3, "transition_gbdt": 4}
    metric["parsimony_rank"] = [
        (transition_rank if outcome == "anomaly_transition" else hourly_rank)[model]
        for outcome, model in zip(metric["outcome"], metric["model"])
    ]

    columns = [
        "selection_stage",
        "outcome",
        "model",
        "parsimony_rank",
        "score_name",
        "mean_cv_score",
        "sd_cv_score",
        "se_cv_score",
        "n_folds",
        "one_se_threshold",
        "selected",
        "selection_rule",
    ]
    result = pd.concat([initial[columns], metric[columns]], ignore_index=True)
    require(len(result) == 20, "Model-selection summary should contain 20 candidate rows")
    selected = set(zip(result.loc[result["selected"], "outcome"], result.loc[result["selected"], "model"]))
    expected = {
        ("hourly_composite", "hour_offset"),
        ("hourly_core", "geometry_ridge"),
        ("hourly_ring", "hour_offset"),
        ("hourly_anomaly", "raw"),
        ("anomaly_transition", "raw"),
    }
    require(selected == expected, f"Unexpected selected models: {selected}")
    return result


def uncertainty_row(
    frame: pd.DataFrame,
    scope_label: str,
    scope_type: str,
    event_id: int | None,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, Any]:
    certified = frame["certified_sign"].ne(0)
    n = int(len(frame))
    n_covered = int(frame["covered"].astype(bool).sum())
    n_certified = int(certified.sum())
    n_certified_correct = int(frame.loc[certified, "certified_correct"].astype(bool).sum())
    return {
        "scope_type": scope_type,
        "scope_label": scope_label,
        "event_time_id": event_id,
        "start_date": start_date,
        "end_date": end_date,
        "n_transitions": n,
        "n_covered": n_covered,
        "coverage": n_covered / n,
        "n_certified": n_certified,
        "certified_fraction": n_certified / n,
        "n_certified_correct": n_certified_correct,
        "certified_sign_accuracy": n_certified_correct / n_certified if n_certified else np.nan,
        "uncertainty_half_width_k": float(((frame["prediction_high"] - frame["prediction_low"]) / 2).mean()),
        "mean_interval_width_k": float((frame["prediction_high"] - frame["prediction_low"]).mean()),
        "formal_gate_scope": scope_label == "combined",
        "coverage_gate_lower_bound": 0.85,
        "coverage_gate_upper_bound": 0.95,
        "certified_accuracy_gate_threshold": 0.90,
        "coverage_within_prespecified_band": 0.85 <= n_covered / n <= 0.95,
        "certified_accuracy_gate_pass": (n_certified_correct / n_certified >= 0.90) if n_certified else False,
        "meets_both_uncertainty_criteria": (
            0.85 <= n_covered / n <= 0.95
            and (n_certified_correct / n_certified >= 0.90 if n_certified else False)
        ),
    }


def build_uncertainty_gate(source_root: Path, chronology: pd.DataFrame) -> pd.DataFrame:
    prediction_path = source_root / "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/validation_2026_transition_predictions.parquet"
    predictions = pd.read_parquet(prediction_path)
    rows = [uncertainty_row(predictions, "combined", "cohort", None, None, None)]
    for cohort in ("expansion", "original"):
        rows.append(
            uncertainty_row(
                predictions[predictions["calibration_cohort"].eq(cohort)],
                cohort,
                "cohort",
                None,
                None,
                None,
            )
        )
    dates = chronology[chronology["design_id"].eq("goes18_goes19_2026")].set_index("event_time_id")
    for event_id, event in predictions.groupby("event_time_id", observed=True, sort=True):
        event_id = int(event_id)
        rows.append(
            uncertainty_row(
                event,
                f"event_{event_id}",
                "event",
                event_id,
                dates.loc[event_id, "start_date"],
                dates.loc[event_id, "end_date"],
            )
        )
    result = pd.DataFrame(rows)
    require(len(result) == 11, "Uncertainty table should contain 3 cohort and 8 event rows")

    frozen = pd.read_csv(
        source_root / "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/validation_2026_uncertainty.csv"
    ).set_index("cohort")
    compared = result.set_index("scope_label")
    require(set(frozen.index) == set(compared.index), "Uncertainty scope labels differ from frozen summary")
    for column in ("n", "coverage", "certified_fraction", "certified_sign_accuracy", "mean_interval_width_k"):
        derived_column = "n_transitions" if column == "n" else column
        require(
            np.allclose(
                frozen.loc[compared.index, column].astype(float),
                compared[derived_column].astype(float),
                atol=1e-12,
                rtol=0,
            ),
            f"Derived uncertainty values differ for {column}",
        )
    return result


def validate_frozen_hashes(source_root: Path) -> dict[str, bool]:
    checks = {
        "original_city_hash": (
            "data/goes18_2022_2024_same_sensor/FROZEN_SELECTION.json",
            "cities",
            "data/goes18_2022_2024_same_sensor/goes_sunset_cities.csv",
        ),
        "expansion_city_hash": (
            "data/goes18_2022_2024_expansion/FROZEN_SELECTION.json",
            "cities",
            "data/goes18_2022_2024_expansion/goes_sunset_cities.csv",
        ),
        "combined_2026_city_hash": (
            "data/goes18_2026_metric_holdout/FROZEN_SELECTION.json",
            "cities",
            "data/goes18_2026_metric_holdout/goes_sunset_cities.csv",
        ),
        "historical_interval_hash": (
            "data/goes18_2022_2024_same_sensor/FROZEN_SELECTION.json",
            "intervals",
            "data/goes18_2022_2024_same_sensor/goes18_2022_2024_intervals.csv",
        ),
        "2025_interval_hash": (
            "data/goes18_2025_western_replication/FROZEN_SELECTION.json",
            "intervals",
            "data/goes18_2025_western_replication/goes18_2025_intervals.csv",
        ),
        "2026_interval_hash": (
            "data/goes18_2026_metric_holdout/FROZEN_SELECTION.json",
            "intervals",
            "data/goes18_2026_metric_holdout/goes_sunset_intervals.csv",
        ),
        "external_city_hash": (
            "data/goes17_2019_2021_external_metric/FROZEN_SELECTION.json",
            "cities",
            "data/goes17_2019_2021_external_metric/goes_sunset_cities.csv",
        ),
        "external_interval_hash": (
            "data/goes17_2019_2021_external_metric/FROZEN_SELECTION.json",
            "intervals",
            "data/goes17_2019_2021_external_metric/goes_sunset_intervals.csv",
        ),
    }
    results: dict[str, bool] = {}
    for label, (manifest_path, hash_key, payload_path) in checks.items():
        manifest = json.loads((source_root / manifest_path).read_text(encoding="utf-8"))
        results[label] = manifest["hashes"][hash_key] == sha256(source_root / payload_path)
        require(results[label], f"Frozen manifest hash failed: {label}")
    return results


def source_inventory(source_root: Path, name_lookup: Path) -> list[Source]:
    source_root_label = (
        "reviewer_repository" if source_root == MANUSCRIPT_ROOT else "original_workspace"
    )
    entries = [
        ("candidate_original", "data/goes18_2022_2024_same_sensor/goes_sunset_cities.csv", "original 51-city candidate metadata"),
        ("candidate_expansion", "data/goes18_2022_2024_expansion/goes_sunset_cities.csv", "expansion 43-city candidate metadata"),
        ("candidate_combined", "data/goes18_2026_metric_holdout/goes_sunset_cities.csv", "combined 94-city candidate metadata"),
        ("candidate_external", "data/goes17_2019_2021_external_metric/goes_sunset_cities.csv", "external 75-city candidate metadata"),
        ("mask_goes18_2026", "data/goes18_2026_metric_holdout/goes_city_grid_mask_summary.csv", "GOES-18 grid-support counts"),
        ("mask_goes19_2026", "data/goes19_2026_metric_holdout/goes_city_grid_mask_summary.csv", "GOES-19 grid-support counts"),
        ("intervals_2022_2024", "data/goes18_2022_2024_same_sensor/goes18_2022_2024_intervals.csv", "31 fixed historical intervals"),
        ("intervals_2025", "data/goes19_2025_holdout/goes19_2025_intervals.csv", "10 fixed 2025 intervals"),
        ("intervals_2026", "data/goes18_2026_metric_holdout/goes_sunset_intervals.csv", "8 prospective 2026 intervals"),
        ("intervals_external", "data/goes17_2019_2021_external_metric/goes_sunset_intervals.csv", "8 external calibration/validation intervals"),
        ("selection_initial", "outputs/grl_deepening_2026/multiplatform_harmonization/derivation_model_selection.csv", "initial model-selection scores"),
        ("selection_metric_aware", "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/model_selection.csv", "metric-specific model-selection scores"),
        ("uncertainty_frozen_summary", "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/validation_2026_uncertainty.csv", "frozen 2026 uncertainty summary"),
        ("uncertainty_predictions", "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/validation_2026_transition_predictions.parquet", "row-level 2026 uncertainty outcomes"),
        ("external_offsets", "outputs/grl_deepening_2026/goes17_goes16_external_metric/frozen_hour_offsets_2019_2020.csv", "frozen external hour offsets"),
        ("external_attrition", "outputs/grl_deepening_2026/goes17_goes16_external_metric/event_attrition.csv", "external event-level attrition"),
        ("external_report", "outputs/grl_deepening_2026/goes17_goes16_external_metric/external_replication_report.json", "external aggregate analysis counts"),
        ("external_goes16_hourly_input", "data/goes16_2019_2021_external_metric/goes_sunset_hourly.parquet", "source-platform input for external calibration membership"),
        ("external_goes17_hourly_input", "data/goes17_2019_2021_external_metric/goes_sunset_hourly.parquet", "reference-platform input for external calibration membership"),
    ]
    sources = [
        Source(source_id, source_root_label, source_root / path, path, role)
        for source_id, path, role in entries
    ]
    for index, stage in enumerate(STAGES):
        if stage.hourly_path is not None:
            sources.append(
                Source(
                    f"stage_hourly_{index + 1}",
                    source_root_label,
                    source_root / stage.hourly_path,
                    stage.hourly_path,
                    f"hourly analysis membership/counts for {stage.stage_id}",
                )
            )
        if stage.transition_path is not None:
            sources.append(
                Source(
                    f"stage_transition_{index + 1}",
                    source_root_label,
                    source_root / stage.transition_path,
                    stage.transition_path,
                    f"transition analysis counts for {stage.stage_id}",
                )
            )
    for target_name, relative_path in FROZEN_COPIES.items():
        sources.append(
            Source(
                f"frozen_copy_{target_name.removesuffix('.json').lower()}",
                source_root_label,
                source_root / relative_path,
                relative_path,
                f"byte-for-byte source for {target_name}",
            )
        )
    try:
        lookup_logical_path = str(name_lookup.relative_to(MANUSCRIPT_ROOT))
        lookup_root_label = "reviewer_repository" if source_root == MANUSCRIPT_ROOT else "manuscript_package"
    except ValueError:
        lookup_logical_path = name_lookup.name
        lookup_root_label = "external_auxiliary_lookup"
    sources.append(
        Source(
            "city_name_lookup",
            lookup_root_label,
            name_lookup,
            lookup_logical_path,
            "uc_id-to-city-name join; coordinates independently checked against frozen candidates",
        )
    )
    unique: dict[tuple[str, str], Source] = {}
    for source in sources:
        unique[(source.root_label, source.logical_path)] = source
    result = sorted(unique.values(), key=lambda source: (source.root_label, source.logical_path))
    for source in result:
        require(source.path.exists(), f"Missing source: {source.path}")
    return result


def copy_frozen_inputs(source_root: Path, frozen_input_dir: Path) -> list[Path]:
    copied = []
    for target_name, relative_path in FROZEN_COPIES.items():
        source = source_root / relative_path
        target = frozen_input_dir / target_name
        shutil.copyfile(source, target)
        require(sha256(source) == sha256(target), f"Frozen copy differs: {target_name}")
        copied.append(target)
    return copied


def freeze_auxiliary_city_lookup(
    source_root: Path, name_lookup: Path, frozen_input_dir: Path
) -> Path:
    """Store only the 94 joined city-name rows needed for package-local reruns."""
    candidate_ids = city_ids(
        read_csv(source_root / "data/goes18_2026_metric_holdout/goes_sunset_cities.csv")
    )
    lookup = read_csv(name_lookup)[["uc_id", "uc_name", "lat", "lon", "region"]]
    subset = lookup[lookup["uc_id"].isin(candidate_ids)].copy()
    require(len(subset) == subset["uc_id"].nunique() == 94, "Auxiliary frozen lookup is not 94 unique cities")
    require(subset["uc_name"].notna().all(), "Auxiliary frozen lookup contains missing names")
    subset["uc_id_sort"] = pd.to_numeric(subset["uc_id"])
    subset = subset.sort_values("uc_id_sort").drop(columns="uc_id_sort").reset_index(drop=True)
    target = frozen_input_dir / "AUXILIARY_UCDB_94_CITY_LOOKUP.csv"
    write_csv(subset, target)
    return target


def dataframe_provenance(sources: Iterable[Source]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_id": source.source_id,
                "root_label": source.root_label,
                "logical_path": source.logical_path,
                "sha256": sha256(source.path),
                "bytes": source.path.stat().st_size,
                "role": source.role,
            }
            for source in sources
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--name-lookup", type=Path, default=DEFAULT_NAME_LOOKUP)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--frozen-input-dir", type=Path, default=DEFAULT_FROZEN_INPUT_DIR)
    args = parser.parse_args()

    source_root = args.source_root.expanduser().resolve()
    name_lookup = args.name_lookup.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    frozen_input_dir = args.frozen_input_dir.expanduser().resolve()
    require(source_root.is_dir(), f"Original source root not found: {source_root}")
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_input_dir.mkdir(parents=True, exist_ok=True)
    if not name_lookup.is_file():
        package_lookup = frozen_input_dir / "AUXILIARY_UCDB_94_CITY_LOOKUP.csv"
        require(package_lookup.is_file(), f"City-name lookup not found: {name_lookup}")
        name_lookup = package_lookup

    sources = source_inventory(source_root, name_lookup)
    frozen_hash_checks = validate_frozen_hashes(source_root)
    chronology = build_interval_chronology(source_root)
    outputs = {
        "fixed_city_candidate_metadata.csv": build_city_metadata(source_root, name_lookup),
        "fixed_interval_chronology.csv": chronology,
        "cohort_attrition_summary.csv": build_attrition_summary(source_root),
        "cohort_event_analysis_counts.csv": build_event_counts(source_root, chronology),
        "model_selection_summary.csv": build_model_selection(source_root),
        "uncertainty_gate_2026_by_cohort_event.csv": build_uncertainty_gate(source_root, chronology),
        "source_provenance_manifest.csv": dataframe_provenance(sources),
    }
    for filename, frame in outputs.items():
        write_csv(frame, output_dir / filename)

    external_offset_source = (
        source_root
        / "outputs/grl_deepening_2026/goes17_goes16_external_metric/frozen_hour_offsets_2019_2020.csv"
    )
    external_offset_target = output_dir / "external_hour_offsets_2019_2020.csv"
    shutil.copyfile(external_offset_source, external_offset_target)
    require(sha256(external_offset_source) == sha256(external_offset_target), "External offset copy is not byte-identical")
    frozen_paths = copy_frozen_inputs(source_root, frozen_input_dir)
    frozen_paths.append(freeze_auxiliary_city_lookup(source_root, name_lookup, frozen_input_dir))

    output_paths = sorted(
        [output_dir / filename for filename in outputs]
        + [external_offset_target]
        + frozen_paths,
        key=lambda path: str(path),
    )

    def artifact_label(path: Path) -> str:
        try:
            return str(path.relative_to(MANUSCRIPT_ROOT))
        except ValueError:
            try:
                return str(Path("output_dir") / path.relative_to(output_dir))
            except ValueError:
                return str(Path("frozen_input_dir") / path.relative_to(frozen_input_dir))

    validation = {
        "status": "pass",
        "deterministic": True,
        "random_seed": None,
        "eligibility_rules": {
            "minimum_core_grid_pixels": MIN_CORE_PIXELS,
            "minimum_ring_grid_pixels": MIN_RING_PIXELS,
            "transition_pre_hours": sorted(PRE_HOURS),
            "transition_late_hours": sorted(LATE_HOURS),
            "minimum_observed_hours_per_window": 2,
            "pooled_uncertainty_coverage_band": [0.85, 0.95],
            "minimum_certified_sign_accuracy": 0.90,
        },
        "frozen_manifest_payload_hash_checks": frozen_hash_checks,
        "table_rows": {filename: int(len(frame)) for filename, frame in outputs.items()},
        "validated_stage_counts": {
            stage_id: {
                "analyzed_cities": counts[0],
                "hourly_city_event_rows": counts[1],
                "eligible_transition_city_events": counts[2],
            }
            for stage_id, counts in EXPECTED_STAGE_COUNTS.items()
        },
        "artifact_sha256": {
            artifact_label(path): sha256(path) for path in output_paths
        },
    }
    validation_path = output_dir / "validation_report.json"
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(validation, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
