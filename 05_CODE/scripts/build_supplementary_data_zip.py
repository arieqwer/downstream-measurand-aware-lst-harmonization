#!/usr/bin/env python3
"""Build the deterministic machine-readable Supplementary Data archive."""

from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "07_SUBMISSION" / "GSIS_supplementary_data.zip"

MEMBERS = [
    "07_SUBMISSION/supplementary_data_README.md",
    "02_EVIDENCE/si_tables/README.md",
    "02_EVIDENCE/si_tables/cohort_attrition_summary.csv",
    "02_EVIDENCE/si_tables/cohort_event_analysis_counts.csv",
    "02_EVIDENCE/si_tables/external_hour_offsets_2019_2020.csv",
    "02_EVIDENCE/si_tables/fixed_city_candidate_metadata.csv",
    "02_EVIDENCE/si_tables/fixed_interval_chronology.csv",
    "02_EVIDENCE/si_tables/model_selection_summary.csv",
    "02_EVIDENCE/si_tables/source_provenance_manifest.csv",
    "02_EVIDENCE/si_tables/uncertainty_gate_2026_by_cohort_event.csv",
    "02_EVIDENCE/si_tables/validation_report.json",
    "02_EVIDENCE/tables/cross_sample_rmse_with_external.csv",
    "02_EVIDENCE/tables/exact_mse_budgets_with_external.csv",
    "02_EVIDENCE/tables/mse_budget_2026_bootstrap_summary.csv",
    "02_EVIDENCE/tables/metric_aware_decision_audit.csv",
    "02_EVIDENCE/external_replication/validation_2021_bootstrap_summary.csv",
    "02_EVIDENCE/external_replication/validation_2021_event_influence.csv",
    "02_EVIDENCE/bootstrap/mse_budget_2026_crossed_bootstrap.parquet",
    "02_EVIDENCE/bootstrap/validation_2021_crossed_bootstrap.parquet",
    "02_EVIDENCE/simulation/README.md",
    "02_EVIDENCE/simulation/covariance_regime_grid.csv",
    "02_EVIDENCE/simulation/covariance_regime_simulation_summary.json",
    "02_EVIDENCE/simulation/covariance_regime_validation.json",
    "02_EVIDENCE/simulation/empirical_cohort_positions.csv",
    "02_EVIDENCE/simulation/simulation_artifact_hashes.json",
]


def main() -> None:
    missing = [member for member in MEMBERS if not (ROOT / member).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing supplementary archive members: {missing}")

    with zipfile.ZipFile(
        OUTPUT,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for member in MEMBERS:
            payload = (ROOT / member).read_bytes()
            info = zipfile.ZipInfo(member, date_time=(2026, 8, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.namelist() == MEMBERS
        assert archive.testzip() is None
    print(f"{OUTPUT.relative_to(ROOT)}: {len(MEMBERS)} files")


if __name__ == "__main__":
    main()
