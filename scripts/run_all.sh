#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repository_root"

python3 05_CODE/scripts/build_si_evidence_tables.py \
  --source-root . \
  --name-lookup 04_PROTOCOLS/frozen_inputs/AUXILIARY_UCDB_94_CITY_LOOKUP.csv
python3 05_CODE/scripts/build_covariance_regime_stress_test.py
python3 05_CODE/scripts/build_submission_figures.py
python3 05_CODE/scripts/build_downstream_metric_framework_figure.py
python3 05_CODE/scripts/build_supplementary_data_zip.py
python3 05_CODE/scripts/validate_reviewer_package.py
python3 -m unittest discover -s 05_CODE/tests -p 'test_metric_aware_harmonization.py' -v

echo "Reviewer-package rebuild and validation passed."
