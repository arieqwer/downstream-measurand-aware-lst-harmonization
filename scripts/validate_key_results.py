from __future__ import annotations

from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
EXT = REPO_ROOT / "data" / "processed" / "extended_outputs_local"


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def main() -> None:
    state = pd.read_csv(EXT / "23_true_night_green_refuge_failure" / "true_night_green_refuge_state_summary.csv")
    high = state[state["veg_group"].eq("high_veg")].set_index("state")
    low = state[state["veg_group"].eq("low_veg")].set_index("state")
    rel = pd.read_csv(EXT / "25_true_night_reliability_index" / "true_night_reliability_group_summary.csv").set_index("veg_group")
    matched = pd.read_csv(EXT / "26_matched_high_low_veg_controls" / "high_low_veg_matched_pair_effects.csv").set_index("outcome")
    exposure = pd.read_csv(EXT / "23_true_night_green_refuge_failure" / "true_night_green_refuge_exposure_period_summary.csv")
    exp_row = exposure[
        exposure["metric"].eq("true_failure_local_t2m_p90")
        & exposure["veg_group"].eq("high_veg")
        & exposure["period"].eq("2021-2025")
    ].iloc[0]
    ame = pd.read_csv(EXT / "72_green_refuge_reliability_pathway" / "green_refuge_pathway_average_marginal_effects.csv")
    resets = pd.read_csv(EXT / "72_green_refuge_reliability_pathway" / "green_refuge_pathway_counterfactual_resets.csv")

    print("Core-ring built-surface anomaly, high-green support")
    print(f"  MLD: {high.loc['MLD', 'mean_core_minus_ring_tb_night_anom']:.3f} °C")
    print(f"  DHD: {high.loc['DHD', 'mean_core_minus_ring_tb_night_anom']:.3f} °C")
    print(f"  Extreme DHD: {high.loc['extreme_DHD', 'mean_core_minus_ring_tb_night_anom']:.3f} °C")
    print()
    print("True-night local P90 and failure rates")
    print(f"  High-green DHD true-night hot exposure: {pct(high.loc['DHD', 'frac_true_health_local_t2m_p90'])}")
    print(f"  High-green DHD failure rate: {pct(high.loc['DHD', 'frac_true_failure_local_t2m_p90'])}")
    print(f"  High-green failure given DHD hot: {pct(rel.loc['high_veg', 'p_failure_given_hot_dhd_pop_weighted_mean'])}")
    print(f"  Low-green failure given DHD hot: {pct(rel.loc['low_veg', 'p_failure_given_hot_dhd_pop_weighted_mean'])}")
    print()
    print("Matched high-minus-low effects")
    print(f"  Compound reliability loss: {matched.loc['compound_failure_loss_dhd_minus_mld', 'mean_high_minus_matched_low']:.4f}")
    print(f"  95% CI: {matched.loc['compound_failure_loss_dhd_minus_mld', 'ci95_low']:.4f} to {matched.loc['compound_failure_loss_dhd_minus_mld', 'ci95_high']:.4f}")
    print()
    print("Population scale, high-green support, 2021-2025")
    print(f"  Mean concurrent represented exposure: {exp_row['mean_concurrent_exposed_population'] / 1e6:.1f} million")
    print(f"  Maximum concurrent represented exposure: {exp_row['max_concurrent_exposed_population'] / 1e6:.1f} million")
    print()
    print("Reliability-pathway average marginal effects")
    for row in ame.itertuples(index=False):
        print(f"  {row.variable}: {row.average_marginal_effect_probability_points_per_1sd:.4f} probability units per 1 s.d.")
    print()
    print("Association-based standardization scale")
    for row in resets.itertuples(index=False):
        print(f"  {row.reset}: {row.represented_resident_8day_intervals / 1e9:.2f} billion represented resident-8-day intervals")


if __name__ == "__main__":
    main()

