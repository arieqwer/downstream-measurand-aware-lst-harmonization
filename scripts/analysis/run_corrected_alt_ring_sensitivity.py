from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_1samp

from analysis_utils import bootstrap_mean_ci


ROOT = Path(__file__).resolve().parents[2]
ALT_PANEL = ROOT / "data/external/alt_ring_gradient_panel.parquet"
PAIRS = ROOT / "data/processed/analysis_outputs/optimal_exact_matched_pairs.csv"
OUT = ROOT / "data/processed/analysis_outputs/corrected_alt_ring_sensitivity.csv"
RANDOM_SEED = 20260714


def main() -> None:
    panel = pd.read_parquet(ALT_PANEL)
    panel["uc_id"] = panel["uc_id"].astype(str)
    panel = panel[panel["core_minus_ring_tb_night_anom"].notna()].copy()
    panel["analysis_state"] = np.select(
        [
            panel["is_extreme_dhd"].astype(bool),
            panel["is_dhd"].astype(bool),
            panel["is_mld"].astype(bool),
        ],
        ["extreme_dhd", "dhd", "mld"],
        default="other",
    )
    panel["night_positive"] = panel["core_minus_ring_tb_night_anom"].gt(0).astype(float)
    pairs = pd.read_csv(PAIRS, dtype={"high_uc_id": str, "low_uc_id": str})
    random = np.random.default_rng(RANDOM_SEED)

    metrics = ["core_minus_ring_tb_night_anom", "night_positive"]
    city_state = (
        panel[panel["analysis_state"].isin(["mld", "dhd", "extreme_dhd"])]
        .groupby(["uc_id", "ring_definition", "analysis_state"], as_index=False)
        .agg(
            n_intervals=("year", "size"),
            core_minus_ring_tb_night_anom=("core_minus_ring_tb_night_anom", "mean"),
            night_positive=("night_positive", "mean"),
        )
    )

    rows = []
    for ring, subset in city_state.groupby("ring_definition", sort=True):
        wide = subset.pivot(index="uc_id", columns="analysis_state")
        for state in ["dhd", "extreme_dhd"]:
            for metric in metrics:
                shifts = pd.DataFrame(
                    {
                        "uc_id": wide.index,
                        "shift": wide[(metric, state)] - wide[(metric, "mld")],
                        "n_mld": wide[("n_intervals", "mld")],
                        "n_stress": wide[("n_intervals", state)],
                    }
                ).dropna()
                shifts = shifts[
                    (shifts["n_mld"] >= 10) & (shifts["n_stress"] >= 10)
                ].set_index("uc_id")
                matched = (
                    pairs.merge(shifts[["shift"]], left_on="high_uc_id", right_index=True)
                    .rename(columns={"shift": "high_shift"})
                    .merge(shifts[["shift"]], left_on="low_uc_id", right_index=True)
                    .rename(columns={"shift": "low_shift"})
                )
                effects = (matched["high_shift"] - matched["low_shift"]).to_numpy(dtype=float)
                ci_low, ci_high = bootstrap_mean_ci(effects, random)
                test = ttest_1samp(effects, popmean=0.0)
                rows.append(
                    {
                        "ring_definition": ring,
                        "contrast": f"{state}_minus_mld",
                        "outcome": metric,
                        "n_pairs": len(effects),
                        "matched_high_minus_low_shift": effects.mean(),
                        "bootstrap_ci95_low": ci_low,
                        "bootstrap_ci95_high": ci_high,
                        "p_value": test.pvalue,
                    }
                )
    result = pd.DataFrame(rows)
    result.to_csv(OUT, index=False)
    print(result.round(5).to_string(index=False))


if __name__ == "__main__":
    main()
