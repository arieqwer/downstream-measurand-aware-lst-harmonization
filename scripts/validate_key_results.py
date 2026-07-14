from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/analysis_outputs"


def close(actual: float, expected: float, atol: float = 5e-6) -> None:
    if not np.isclose(float(actual), expected, atol=atol, rtol=0):
        raise AssertionError(f"Expected {expected}, found {actual}")


def main() -> None:
    state = pd.read_csv(SOURCE / "differential_thermal_decay_state_summary.csv")
    state = state[
        state["weighting"].eq("city")
        & state["sample"].eq("all_intervals")
        & state["high_green"].eq(1)
    ]
    values = state.set_index("analysis_state")["mean_differential_decay_1e4_h"]
    close(values["mld"], 0.7562507214)
    close(values["dhd"], -0.1169999051)
    close(values["extreme_dhd"], -0.2804215420)

    terms = pd.read_csv(SOURCE / "differential_thermal_decay_twfe_terms.csv").set_index("term")
    close(terms.loc["dhd_x_high_green", "estimate"], -0.3009647810)
    close(terms.loc["extreme_x_high_green", "estimate"], -0.4331774467)

    quartiles = pd.read_csv(SOURCE / "differential_thermal_decay_storage_quartiles.csv")
    quartiles = quartiles[quartiles["contrast"].eq("dhd_minus_mld")].set_index("storage_quartile")
    close(quartiles.loc["Q1 lowest", "mean_differential_decay_shift_1e4_h"], -0.1478935283)
    close(quartiles.loc["Q4 highest", "mean_differential_decay_shift_1e4_h"], -1.3747573446)

    water = pd.read_csv(SOURCE / "differential_decay_water_support_heterogeneity.csv")
    water = water[water["term"].eq("dhd_x_built_form_storage_score")].set_index("water_support_tertile")
    close(water.loc["Low", "estimate"], -0.7557346219)
    close(water.loc["High", "estimate"], -0.2813310540)

    memory = pd.read_csv(SOURCE / "stress_memory_twfe_terms.csv")
    duration = memory[memory["model"].eq("dhd_duration_differential_decay_1e4_h")].set_index("term")
    close(duration.loc["duration_excess_capped", "estimate"], -0.0717723650)
    close(duration.loc["duration_x_storage", "estimate"], -0.0519066264)

    concurrence = pd.read_csv(SOURCE / "corrected_inversion_concurrence_summary.csv").set_index("inversion_threshold_c")
    close(concurrence.loc[0.25, "maximum_concurrent_represented_population"], 101683614.2393, 0.01)
    nulls = pd.read_csv(SOURCE / "severe_inversion_timing_null_summary.csv")
    strict = nulls[
        nulls["null_name"].eq("DHD and true-night-heat timing preserved")
        & nulls["statistic"].eq("max_population")
    ].iloc[0]
    close(strict["empirical_p_one_sided"], 0.0598802395)

    print("Key-result validation passed.")


if __name__ == "__main__":
    main()
