#!/usr/bin/env bash
set -euo pipefail

python scripts/make_main_and_selected_supplementary_figures.py
python scripts/make_figure_5_reliability_pathway.py
python scripts/make_supplementary_figures_s1_s2.py
python scripts/make_supplementary_figure_s7_robustness.py

