#!/usr/bin/env python3
"""Independently validate the retained reviewer reproducibility package.

This script deliberately does not import the analysis pipeline.  It rebuilds the
five-cohort hourly and transition diagnostics from the retained row-level
prediction files, verifies the exact downstream MSE identity, audits the 2026
uncertainty gate, checks both saved crossed-bootstrap archives, and validates
all source-manifest hashes that can be resolved locally.

Examples
--------
Run inside a self-contained review repository::

    python3 05_CODE/scripts/validate_reviewer_package.py

Audit the manuscript package while its retained source tree is still separate::

    python3 05_CODE/scripts/validate_reviewer_package.py \
      --source-root ../thermal_hysteresis_research
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
ABSOLUTE_TOLERANCE = 1e-12
IDENTITY_TOLERANCE = 2e-12
BOOTSTRAP_DRAWS = 5_000


@dataclass(frozen=True)
class Sample:
    name: str
    logical_path: str
    core_estimate: str
    ring_estimate: str
    local_fallback: str | None = None


SAMPLES = (
    Sample(
        "2021 external GOES17/16",
        "outputs/grl_deepening_2026/goes17_goes16_external_metric/"
        "validation_2021_hourly_predictions.parquet",
        "pred_core",
        "pred_ring",
        "02_EVIDENCE/external_replication/validation_2021_hourly_predictions.parquet",
    ),
    Sample(
        "2022-2024 expansion GOES18/16",
        "outputs/grl_deepening_2026/multiplatform_expanded_validation/"
        "historical_expanded_predictions.parquet",
        "pred_core",
        "pred_ring",
    ),
    Sample(
        "2025 original GOES18/19",
        "outputs/grl_deepening_2026/multiplatform_harmonization/"
        "validation_2025_predictions.parquet",
        "pred_core",
        "pred_ring",
    ),
    Sample(
        "2025 expansion GOES18/19",
        "outputs/grl_deepening_2026/multiplatform_expanded_validation/"
        "validation_expanded_predictions.parquet",
        "pred_core",
        "pred_ring",
    ),
    Sample(
        "2026 combined GOES18/19",
        "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/"
        "validation_2026_hourly_predictions.parquet",
        "metric_pred_core",
        "metric_pred_ring",
    ),
)


class Audit:
    """Collect explicit pass/fail results and fail once after the full audit."""

    def __init__(self) -> None:
        self.checks: list[dict[str, object]] = []

    def check(self, name: str, passed: bool, detail: object) -> None:
        self.checks.append({"check": name, "passed": bool(passed), "detail": detail})

    def require(self, name: str, passed: bool, detail: object) -> None:
        self.check(name, passed, detail)
        if not passed:
            raise AssertionError(f"{name}: {detail}")

    def report(self) -> dict[str, object]:
        failed = [item for item in self.checks if not item["passed"]]
        return {
            "status": "pass" if not failed else "fail",
            "checks_passed": len(self.checks) - len(failed),
            "checks_failed": len(failed),
            "checks": self.checks,
        }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path.resolve(strict=False))
        if key not in seen:
            result.append(path)
            seen.add(key)
    return result


def resolve_sample_path(root: Path, source_root: Path, sample: Sample) -> Path:
    candidates = [root / sample.logical_path, source_root / sample.logical_path]
    if sample.local_fallback:
        candidates.append(root / sample.local_fallback)
    for candidate in unique_paths(candidates):
        if candidate.is_file():
            return candidate
    rendered = "\n  - ".join(str(path) for path in unique_paths(candidates))
    raise FileNotFoundError(
        f"No retained row-level prediction file for {sample.name}. Tried:\n  - {rendered}"
    )


def prepare_hourly(path: Path, core_estimate: str, ring_estimate: str) -> pd.DataFrame:
    frame = pd.read_parquet(path).copy()
    required = {
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "target_hour_from_sunset",
        "target_core",
        "target_ring",
        "source_core",
        "source_ring",
        core_estimate,
        ring_estimate,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise AssertionError(f"{path} is missing columns: {missing}")
    frame["target_anomaly"] = frame["target_core"] - frame["target_ring"]
    frame["source_anomaly"] = frame["source_core"] - frame["source_ring"]
    frame["pred_core"] = frame[core_estimate]
    frame["pred_ring"] = frame[ring_estimate]
    frame["pred_anomaly"] = frame["pred_core"] - frame["pred_ring"]
    return frame


def transition_frame(hourly: pd.DataFrame) -> pd.DataFrame:
    """Rebuild the fixed pre (-3:-1 h) to late (+4:+6 h) transition."""
    frame = hourly.copy()
    frame["window"] = np.select(
        [
            frame["target_hour_from_sunset"].between(-3, -1),
            frame["target_hour_from_sunset"].between(4, 6),
        ],
        ["pre", "late"],
        default="other",
    )
    frame = frame[frame["window"].isin(["pre", "late"])]
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
    ]
    grouped = (
        frame.groupby(keys, observed=True)
        .agg(
            **{column: (column, "mean") for column in measures},
            n_hours=("target_hour_from_sunset", "nunique"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["n_hours"].ge(2)]
    index = ["uc_id", "event_year", "event_step8", "event_time_id"]
    wide = grouped.pivot(index=index, columns="window")
    wide.columns = [f"{name}_{window}" for name, window in wide.columns]
    wide = wide.reset_index()
    for prefix in ("target", "source", "pred"):
        for component in ("core", "ring", "anomaly"):
            wide[f"{prefix}_{component}_transition"] = (
                wide[f"{prefix}_{component}_late"]
                - wide[f"{prefix}_{component}_pre"]
            )
    return wide.dropna(
        subset=[
            "target_anomaly_transition",
            "source_anomaly_transition",
            "pred_anomaly_transition",
        ]
    )


def moments(core_error: np.ndarray, ring_error: np.ndarray) -> dict[str, float]:
    core_bias = float(np.mean(core_error))
    ring_bias = float(np.mean(ring_error))
    core_variance = float(np.mean((core_error - core_bias) ** 2))
    ring_variance = float(np.mean((ring_error - ring_bias) ** 2))
    covariance = float(
        np.mean((core_error - core_bias) * (ring_error - ring_bias))
    )
    differential_bias_squared = (core_bias - ring_bias) ** 2
    derived_error = core_error - ring_error
    derived_mse = float(np.mean(derived_error**2))
    identity_mse = (
        core_variance
        + ring_variance
        - 2 * covariance
        + differential_bias_squared
    )
    return {
        "core_bias_k": core_bias,
        "ring_bias_k": ring_bias,
        "core_variance_k2": core_variance,
        "ring_variance_k2": ring_variance,
        "core_ring_covariance_k2": covariance,
        "differential_bias_squared_k2": differential_bias_squared,
        "derived_mse_k2": derived_mse,
        "identity_residual_k2": derived_mse - identity_mse,
    }


def performance_and_budget(frame: pd.DataFrame, scope: str) -> dict[str, float | int | str]:
    suffix = "" if scope == "hourly" else "_transition"
    raw_core = (
        frame[f"source_core{suffix}"] - frame[f"target_core{suffix}"]
    ).to_numpy(dtype=float)
    raw_ring = (
        frame[f"source_ring{suffix}"] - frame[f"target_ring{suffix}"]
    ).to_numpy(dtype=float)
    harm_core = (
        frame[f"pred_core{suffix}"] - frame[f"target_core{suffix}"]
    ).to_numpy(dtype=float)
    harm_ring = (
        frame[f"pred_ring{suffix}"] - frame[f"target_ring{suffix}"]
    ).to_numpy(dtype=float)
    raw_anomaly = raw_core - raw_ring
    harm_anomaly = harm_core - harm_ring

    raw = moments(raw_core, raw_ring)
    harm = moments(harm_core, harm_ring)
    variance_gain = (
        raw["core_variance_k2"]
        - harm["core_variance_k2"]
        + raw["ring_variance_k2"]
        - harm["ring_variance_k2"]
    )
    bias_gain = (
        raw["differential_bias_squared_k2"]
        - harm["differential_bias_squared_k2"]
    )
    covariance_penalty = 2 * (
        raw["core_ring_covariance_k2"] - harm["core_ring_covariance_k2"]
    )
    net_gain = raw["derived_mse_k2"] - harm["derived_mse_k2"]
    budget_sum = variance_gain + bias_gain - covariance_penalty

    def rmse(values: np.ndarray) -> float:
        return float(np.sqrt(np.mean(values**2)))

    raw_core_rmse = rmse(raw_core)
    harm_core_rmse = rmse(harm_core)
    raw_ring_rmse = rmse(raw_ring)
    harm_ring_rmse = rmse(harm_ring)
    raw_anomaly_rmse = rmse(raw_anomaly)
    harm_anomaly_rmse = rmse(harm_anomaly)
    return {
        "scope": scope,
        "n": int(len(frame)),
        "raw_core_bias_k": raw["core_bias_k"],
        "raw_ring_bias_k": raw["ring_bias_k"],
        "harm_core_bias_k": harm["core_bias_k"],
        "harm_ring_bias_k": harm["ring_bias_k"],
        "raw_core_variance_k2": raw["core_variance_k2"],
        "raw_ring_variance_k2": raw["ring_variance_k2"],
        "harm_core_variance_k2": harm["core_variance_k2"],
        "harm_ring_variance_k2": harm["ring_variance_k2"],
        "raw_covariance_k2": raw["core_ring_covariance_k2"],
        "harm_covariance_k2": harm["core_ring_covariance_k2"],
        "raw_differential_bias_squared_k2": raw[
            "differential_bias_squared_k2"
        ],
        "harm_differential_bias_squared_k2": harm[
            "differential_bias_squared_k2"
        ],
        "raw_downstream_mse_k2": raw["derived_mse_k2"],
        "harm_downstream_mse_k2": harm["derived_mse_k2"],
        "component_variance_gain_k2": variance_gain,
        "differential_bias_gain_k2": bias_gain,
        "covariance_loss_penalty_k2": covariance_penalty,
        "net_downstream_mse_gain_k2": net_gain,
        "net_downstream_mse_gain_fraction": net_gain / raw["derived_mse_k2"],
        "budget_sum_k2": budget_sum,
        "budget_closure_residual_k2": net_gain - budget_sum,
        "raw_identity_residual_k2": raw["identity_residual_k2"],
        "harm_identity_residual_k2": harm["identity_residual_k2"],
        "raw_core_rmse_k": raw_core_rmse,
        "harm_core_rmse_k": harm_core_rmse,
        "core_rmse_reduction_fraction": 1 - harm_core_rmse / raw_core_rmse,
        "raw_ring_rmse_k": raw_ring_rmse,
        "harm_ring_rmse_k": harm_ring_rmse,
        "ring_rmse_reduction_fraction": 1 - harm_ring_rmse / raw_ring_rmse,
        "raw_anomaly_rmse_k": raw_anomaly_rmse,
        "harm_anomaly_rmse_k": harm_anomaly_rmse,
        "anomaly_rmse_reduction_fraction": 1
        - harm_anomaly_rmse / raw_anomaly_rmse,
        "raw_error_correlation": float(np.corrcoef(raw_core, raw_ring)[0, 1]),
        "harm_error_correlation": float(np.corrcoef(harm_core, harm_ring)[0, 1]),
        "mean_raw_anomaly_error_k": float(np.mean(raw_anomaly)),
        "mean_harm_anomaly_error_k": float(np.mean(harm_anomaly)),
    }


def rebuild_tables(
    root: Path, source_root: Path
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    budget_rows: list[dict[str, object]] = []
    rmse_rows: list[dict[str, object]] = []
    paths: dict[str, str] = {}
    for sample in SAMPLES:
        path = resolve_sample_path(root, source_root, sample)
        paths[sample.name] = str(path.resolve())
        hourly = prepare_hourly(path, sample.core_estimate, sample.ring_estimate)
        transition = transition_frame(hourly)
        for scope, frame in (("hourly", hourly), ("transition", transition)):
            result = performance_and_budget(frame, scope)
            budget_rows.append(
                {
                    "sample": sample.name,
                    "n_cities": int(frame["uc_id"].nunique()),
                    "n_events": int(frame["event_time_id"].nunique()),
                    **result,
                }
            )
        hourly_result = budget_rows[-2]
        for component in ("core", "ring", "anomaly"):
            rmse_rows.append(
                {
                    "sample": sample.name,
                    "component": component,
                    "raw_rmse_k": hourly_result[f"raw_{component}_rmse_k"],
                    "corrected_rmse_k": hourly_result[f"harm_{component}_rmse_k"],
                    "rmse_reduction_fraction": hourly_result[
                        f"{component}_rmse_reduction_fraction"
                    ],
                }
            )
    return pd.DataFrame(budget_rows), pd.DataFrame(rmse_rows), paths


def compare_saved_table(
    audit: Audit,
    name: str,
    computed: pd.DataFrame,
    expected: pd.DataFrame,
    keys: list[str],
) -> None:
    computed_keys = set(map(tuple, computed[keys].itertuples(index=False, name=None)))
    expected_keys = set(map(tuple, expected[keys].itertuples(index=False, name=None)))
    audit.require(
        f"{name} keys",
        computed_keys == expected_keys,
        {
            "computed_rows": len(computed),
            "saved_rows": len(expected),
            "missing": sorted(expected_keys - computed_keys),
            "unexpected": sorted(computed_keys - expected_keys),
        },
    )
    computed_indexed = computed.set_index(keys)
    maximum_difference = 0.0
    compared_values = 0
    mismatches: list[dict[str, object]] = []
    for _, saved_row in expected.iterrows():
        key = tuple(saved_row[column] for column in keys)
        lookup_key: object = key[0] if len(key) == 1 else key
        rebuilt_row = computed_indexed.loc[lookup_key]
        for column in expected.columns:
            if column in keys or column not in computed.columns:
                continue
            saved_value = saved_row[column]
            if pd.isna(saved_value):
                continue
            rebuilt_value = rebuilt_row[column]
            if isinstance(saved_value, (str, np.str_)):
                equal = str(rebuilt_value) == str(saved_value)
                difference = 0.0 if equal else float("inf")
            else:
                difference = abs(float(rebuilt_value) - float(saved_value))
                equal = difference <= ABSOLUTE_TOLERANCE
                maximum_difference = max(maximum_difference, difference)
            compared_values += 1
            if not equal and len(mismatches) < 20:
                mismatches.append(
                    {
                        "key": key,
                        "column": column,
                        "rebuilt": rebuilt_value,
                        "saved": saved_value,
                        "absolute_difference": difference,
                    }
                )
    audit.require(
        f"{name} values",
        not mismatches,
        {
            "values_compared": compared_values,
            "maximum_absolute_difference": maximum_difference,
            "tolerance": ABSOLUTE_TOLERANCE,
            "mismatches": mismatches,
        },
    )


def validate_rebuilt_results(
    audit: Audit, root: Path, budgets: pd.DataFrame, rmse: pd.DataFrame
) -> None:
    expected_rmse = pd.read_csv(
        root / "02_EVIDENCE/tables/cross_sample_rmse_with_external.csv"
    )
    expected_budgets = pd.read_csv(
        root / "02_EVIDENCE/tables/exact_mse_budgets_with_external.csv"
    )
    compare_saved_table(
        audit,
        "five-cohort hourly RMSE",
        rmse,
        expected_rmse,
        ["sample", "component"],
    )
    compare_saved_table(
        audit,
        "five-cohort exact MSE budgets",
        budgets,
        expected_budgets,
        ["sample", "scope"],
    )
    closure_columns = [
        "budget_closure_residual_k2",
        "raw_identity_residual_k2",
        "harm_identity_residual_k2",
    ]
    maximum_closure = float(budgets[closure_columns].abs().to_numpy().max())
    audit.require(
        "recomputed exact MSE identities",
        maximum_closure <= IDENTITY_TOLERANCE,
        {
            "maximum_absolute_residual_k2": maximum_closure,
            "tolerance_k2": IDENTITY_TOLERANCE,
            "identities_checked": len(budgets) * len(closure_columns),
        },
    )


def validate_gate(audit: Audit, root: Path, source_root: Path) -> None:
    logical = Path(
        "outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/"
        "validation_2026_transition_predictions.parquet"
    )
    candidates = [root / logical, source_root / logical]
    path = next((item for item in unique_paths(candidates) if item.is_file()), None)
    if path is None:
        rendered = "\n  - ".join(str(item) for item in unique_paths(candidates))
        raise FileNotFoundError(
            "No retained 2026 transition predictions for the gate audit. Tried:\n"
            f"  - {rendered}"
        )
    frame = pd.read_parquet(path)
    required = {"covered", "certified_sign", "certified_correct"}
    missing = sorted(required - set(frame.columns))
    audit.require("2026 gate columns", not missing, {"missing": missing, "path": str(path)})
    computed = {
        "n_transitions": int(len(frame)),
        "n_covered": int(frame["covered"].astype(bool).sum()),
        "n_certified": int(frame["certified_sign"].fillna(0).ne(0).sum()),
        "n_certified_correct": int(frame["certified_correct"].astype(bool).sum()),
    }
    expected = {
        "n_transitions": 588,
        "n_covered": 529,
        "n_certified": 180,
        "n_certified_correct": 174,
    }
    audit.require("recomputed 2026 gate counts", computed == expected, computed)

    saved = pd.read_csv(
        root / "02_EVIDENCE/si_tables/uncertainty_gate_2026_by_cohort_event.csv"
    )
    combined = saved[
        saved["scope_type"].eq("cohort") & saved["scope_label"].eq("combined")
    ]
    audit.require("saved combined gate row", len(combined) == 1, {"rows": len(combined)})
    row = combined.iloc[0]
    saved_counts = {key: int(row[key]) for key in expected}
    audit.require("saved 2026 gate counts", saved_counts == expected, saved_counts)
    audit.require(
        "saved 2026 gate fractions",
        abs(float(row["coverage"]) - 529 / 588) <= ABSOLUTE_TOLERANCE
        and abs(float(row["certified_fraction"]) - 180 / 588)
        <= ABSOLUTE_TOLERANCE
        and abs(float(row["certified_sign_accuracy"]) - 174 / 180)
        <= ABSOLUTE_TOLERANCE,
        {
            "coverage": float(row["coverage"]),
            "certified_fraction": float(row["certified_fraction"]),
            "certified_sign_accuracy": float(row["certified_sign_accuracy"]),
        },
    )


def validate_bootstrap_archive(
    audit: Audit,
    label: str,
    draw_path: Path,
    summary_path: Path,
    expected_scope_n: dict[str, int],
) -> None:
    draws = pd.read_parquet(draw_path)
    required = {
        "iteration",
        "scope",
        "n",
        "budget_closure_residual_k2",
        "raw_identity_residual_k2",
        "harm_identity_residual_k2",
    }
    missing = sorted(required - set(draws.columns))
    audit.require(f"{label} bootstrap columns", not missing, {"missing": missing})
    scope_draws = draws.groupby("scope", observed=True)["iteration"].nunique().to_dict()
    scope_rows = draws.groupby("scope", observed=True).size().to_dict()
    scope_n = draws.groupby("scope", observed=True)["n"].unique().to_dict()
    structure_ok = (
        len(draws) == 2 * BOOTSTRAP_DRAWS
        and scope_draws == {"hourly": BOOTSTRAP_DRAWS, "transition": BOOTSTRAP_DRAWS}
        and scope_rows == {"hourly": BOOTSTRAP_DRAWS, "transition": BOOTSTRAP_DRAWS}
        and all(
            len(scope_n[scope]) == 1 and int(scope_n[scope][0]) == expected
            for scope, expected in expected_scope_n.items()
        )
    )
    audit.require(
        f"{label} bootstrap structure",
        structure_ok,
        {
            "rows": len(draws),
            "unique_iterations_by_scope": scope_draws,
            "rows_by_scope": scope_rows,
            "n_by_scope": {key: value.tolist() for key, value in scope_n.items()},
        },
    )
    closure_columns = [
        "budget_closure_residual_k2",
        "raw_identity_residual_k2",
        "harm_identity_residual_k2",
    ]
    maximum_closure = float(draws[closure_columns].abs().to_numpy().max())
    audit.require(
        f"{label} bootstrap identities",
        np.isfinite(maximum_closure) and maximum_closure <= IDENTITY_TOLERANCE,
        {
            "maximum_absolute_residual_k2": maximum_closure,
            "tolerance_k2": IDENTITY_TOLERANCE,
            "identities_checked": len(draws) * len(closure_columns),
        },
    )

    summary = pd.read_csv(summary_path)
    summary_mismatches: list[dict[str, object]] = []
    maximum_difference = 0.0
    for _, row in summary.iterrows():
        scope = str(row["scope"])
        metric = str(row["metric"])
        if metric not in draws.columns:
            summary_mismatches.append(
                {"scope": scope, "metric": metric, "reason": "metric absent from draws"}
            )
            continue
        values = draws.loc[draws["scope"].eq(scope), metric]
        rebuilt = {
            "estimate": float(values.mean()),
            "ci95_low": float(values.quantile(0.025)),
            "ci95_high": float(values.quantile(0.975)),
            "probability_gt_zero": float((values > 0).mean()),
            "n_bootstrap": int(
                draws.loc[draws["scope"].eq(scope), "iteration"].nunique()
            ),
        }
        for column, value in rebuilt.items():
            difference = abs(float(row[column]) - float(value))
            maximum_difference = max(maximum_difference, difference)
            if difference > ABSOLUTE_TOLERANCE:
                summary_mismatches.append(
                    {
                        "scope": scope,
                        "metric": metric,
                        "field": column,
                        "rebuilt": value,
                        "saved": row[column],
                        "absolute_difference": difference,
                    }
                )
    audit.require(
        f"{label} bootstrap summary",
        not summary_mismatches,
        {
            "summary_rows": len(summary),
            "maximum_absolute_difference": maximum_difference,
            "tolerance": ABSOLUTE_TOLERANCE,
            "mismatches": summary_mismatches[:20],
        },
    )


def source_candidates(
    root: Path, source_root: Path, root_label: str, logical_path: str
) -> list[Path]:
    logical = Path(logical_path)
    candidates = [root / logical, source_root / logical]
    if root_label in {"manuscript_package", "reviewer_repository"}:
        candidates.insert(0, root / logical)
    if root_label == "external_auxiliary_lookup":
        candidates.extend(
            [
                root.parent / logical,
                root.parent.parent / logical,
                source_root.parent / logical,
                source_root.parent.parent / logical,
            ]
        )
    return unique_paths(candidates)


def validate_source_manifest(
    audit: Audit, root: Path, source_root: Path
) -> dict[str, object]:
    manifest_path = root / "02_EVIDENCE/si_tables/source_provenance_manifest.csv"
    manifest = pd.read_csv(manifest_path)
    verified: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    mismatches: list[dict[str, object]] = []
    for _, row in manifest.iterrows():
        candidates = source_candidates(
            root, source_root, str(row["root_label"]), str(row["logical_path"])
        )
        path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if path is None:
            unresolved.append(
                {
                    "source_id": row["source_id"],
                    "logical_path": row["logical_path"],
                }
            )
            continue
        observed_hash = sha256(path)
        observed_bytes = path.stat().st_size
        if observed_hash != row["sha256"] or observed_bytes != int(row["bytes"]):
            mismatches.append(
                {
                    "source_id": row["source_id"],
                    "path": str(path),
                    "expected_sha256": row["sha256"],
                    "observed_sha256": observed_hash,
                    "expected_bytes": int(row["bytes"]),
                    "observed_bytes": observed_bytes,
                }
            )
        else:
            verified.append({"source_id": row["source_id"], "path": str(path)})
    audit.require(
        "resolved source provenance hashes",
        not mismatches and bool(verified),
        {
            "manifest_rows": len(manifest),
            "verified": len(verified),
            "unresolved": len(unresolved),
            "mismatches": mismatches,
        },
    )
    return {
        "manifest_rows": len(manifest),
        "verified": len(verified),
        "unresolved": unresolved,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Reviewer-package root (default: inferred from this script).",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help=(
            "Optional retained source root when auditing before the row-level files "
            "are copied into the reviewer package."
        ),
    )
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    source_root = (
        args.source_root.expanduser().resolve() if args.source_root else root
    )

    audit = Audit()
    try:
        budgets, rmse, prediction_paths = rebuild_tables(root, source_root)
        validate_rebuilt_results(audit, root, budgets, rmse)
        validate_gate(audit, root, source_root)
        validate_bootstrap_archive(
            audit,
            "2026 prospective",
            root / "02_EVIDENCE/bootstrap/mse_budget_2026_crossed_bootstrap.parquet",
            root / "02_EVIDENCE/tables/mse_budget_2026_bootstrap_summary.csv",
            {"hourly": 5_744, "transition": 588},
        )
        validate_bootstrap_archive(
            audit,
            "2021 external",
            root / "02_EVIDENCE/bootstrap/validation_2021_crossed_bootstrap.parquet",
            root / "02_EVIDENCE/external_replication/validation_2021_bootstrap_summary.csv",
            {"hourly": 2_571, "transition": 246},
        )
        source_hashes = validate_source_manifest(audit, root, source_root)
    except Exception as exc:
        audit.check("audit completed", False, f"{type(exc).__name__}: {exc}")
        result = audit.report()
        result.update({"root": str(root), "source_root": str(source_root)})
        print(json.dumps(result, indent=2, default=str))
        raise SystemExit(1) from exc

    result = audit.report()
    result.update(
        {
            "root": str(root),
            "source_root": str(source_root),
            "prediction_files": prediction_paths,
            "source_provenance": source_hashes,
            "cohorts_recomputed": len(SAMPLES),
            "budget_rows_recomputed": len(budgets),
            "rmse_rows_recomputed": len(rmse),
        }
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
