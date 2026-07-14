#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" scripts/make_upgrade_figures.py
"$PYTHON_BIN" scripts/make_upgrade_supplementary_figures.py
"$PYTHON_BIN" scripts/export_supplementary_tables.py
"$PYTHON_BIN" scripts/validate_key_results.py
"$PYTHON_BIN" scripts/build_data_manifest.py --verify
