from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/analysis_outputs"
OUTPUT = ROOT / "outputs/tables"


def tagged(frame: pd.DataFrame, section: str) -> pd.DataFrame:
    result = frame.copy()
    result.insert(0, "section", section)
    return result


def write(table_id: str, frames: list[pd.DataFrame]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    pd.concat(frames, ignore_index=True, sort=False).to_csv(
        OUTPUT / f"Table_{table_id}_source.csv", index=False
    )


def table_s1() -> None:
    rows = [
        ["GHS-UCDB R2024A", "Urban-centre polygons; 2025 population; region, income and morphology metadata", "Core geometry, population weighting, matching and built-form variables"],
        ["Terra MOD11A2 C6.1", "8-day, 1 km; LST_Day_1km and LST_Night_1km", "Built-associated core/ring LST and apparent thermal decay"],
        ["Terra MOD13A2 C6.1", "16-day, 1 km NDVI", "Vegetation-associated support mask (NDVI > 0.30)"],
        ["GHS-BUILT-S R2023A", "100 m, 2015 epoch", "Built-presence support mask for MODIS summaries"],
        ["ERA5-Land", "Hourly meteorology; daily land variables", "True-night 2 m temperature, VPD, precipitation and root-zone soil moisture"],
        ["TerraClimate", "Monthly, approximately 4 km", "Long-term AET/(AET + DEF) water-support ratio"],
        ["Global LCZ", "100 m", "Compact-LCZ share and urban-form diagnostics"],
        ["AH4GUC", "1 km, hourly", "Nighttime anthropogenic-heat diagnostic in covered cities"],
    ]
    write("S1", [pd.DataFrame(rows, columns=["product", "resolution_content", "analytical_role"])])


def table_s2() -> None:
    rows = [
        ["Source city-interval panel before complete-case outcome rule", "5,862,378", "Includes missing continuous nighttime outcomes"],
        ["Complete-case core-ring nighttime panel", "5,232,783 intervals; 5,496 cities", "Missing outcomes excluded, never coded as non-events"],
        ["Higher vegetation support", "2,769 cities", "Above median 10-20 km ring vegetation support"],
        ["Lower vegetation support", "2,727 cities", "Below median 10-20 km ring vegetation support"],
        ["Paired day/night focal-state decay panel", "1,162,516 intervals; 5,440 cities", "Valid core and ring day/night built-associated LST"],
        ["Unique matched sample", "1,357 pairs", "Optimal one-to-one assignment without replacement"],
        ["Built-form mechanism sample", "623,842 intervals; 2,769 cities", "Higher-support cities with complete morphology data"],
        ["Coupled water-support model", "623,613 intervals; 2,768 cities", "Complete TerraClimate water support"],
    ]
    write("S2", [pd.DataFrame(rows, columns=["analysis_stage", "sample", "definition"])])


def table_s3() -> None:
    state = pd.read_csv(SOURCE / "differential_thermal_decay_state_summary.csv")
    state = state[state["weighting"].eq("city")]
    terms = pd.read_csv(SOURCE / "differential_thermal_decay_twfe_terms.csv")
    selected = terms[terms["term"].isin([
        "dhd_x_high_green",
        "extreme_x_high_green",
        "dhd_x_green_support",
        "extreme_x_green_support",
    ])]
    write("S3", [tagged(state, "state_summary"), tagged(selected, "fixed_effects")])


def table_s4() -> None:
    balance = pd.read_csv(SOURCE / "optimal_matching_balance.csv")
    matched = pd.read_csv(SOURCE / "matched_differential_thermal_decay_results.csv")
    quantiles = pd.read_csv(SOURCE / "matched_distributional_quantile_results.csv")
    quantiles = quantiles[quantiles["minimum_intervals_per_state"].eq(5)]
    transitions = pd.read_csv(SOURCE / "matched_transition_results.csv")
    write("S4", [
        tagged(balance, "matching_balance"),
        tagged(matched, "matched_decay"),
        tagged(quantiles, "matched_quantiles"),
        tagged(transitions, "inversion_transitions"),
    ])


def table_s5() -> None:
    loadings = pd.read_csv(SOURCE / "built_form_storage_score_loadings.csv")
    quartiles = pd.read_csv(SOURCE / "differential_thermal_decay_storage_quartiles.csv")
    water = pd.read_csv(SOURCE / "differential_decay_water_support_heterogeneity.csv")
    coupled = pd.read_csv(SOURCE / "coupled_water_storage_interaction.csv")
    selected_terms = [
        "dhd_x_built_form_storage_score",
        "extreme_x_built_form_storage_score",
        "dhd_x_water_support",
        "extreme_x_water_support",
        "dhd_x_storage_x_water_support",
        "extreme_x_storage_x_water_support",
    ]
    coupled = coupled[coupled["term"].isin(selected_terms)]
    write("S5", [
        tagged(loadings, "storage_pca"),
        tagged(quartiles, "storage_quartiles"),
        tagged(water, "water_support_heterogeneity"),
        tagged(coupled, "coupled_model"),
    ])


def table_s6() -> None:
    memory = pd.read_csv(SOURCE / "stress_memory_twfe_terms.csv")
    duration = memory[
        memory["model"].eq("dhd_duration_differential_decay_1e4_h")
        & memory["term"].isin(["duration_excess_capped", "duration_x_storage"])
    ]
    post = memory[
        memory["model"].eq("post_dhd_memory_inversion_0p25")
        & memory["term"].str.fullmatch(r"post_dhd_lag[1-4]")
    ]
    write("S6", [tagged(duration, "duration"), tagged(post, "post_stress_memory")])


def table_s7() -> None:
    sampling = pd.read_csv(SOURCE / "differential_thermal_decay_sampling_sensitivity.csv")
    sampling = sampling[sampling["term"].eq("dhd_x_built_form_storage_score")]
    rings = pd.read_csv(SOURCE / "corrected_alt_ring_sensitivity.csv")
    rings = rings[rings["outcome"].eq("core_minus_ring_tb_night_anom")]
    subgroup = pd.read_csv(SOURCE / "differential_thermal_decay_subgroup_interactions.csv")
    regions = subgroup[
        subgroup["subgroup_type"].eq("UN_SDG_region")
        & subgroup["term"].eq("dhd_x_built_form_storage_score")
    ]
    periods = subgroup[subgroup["subgroup_type"].eq("period")]
    write("S7", [
        tagged(sampling, "sampling_sensitivity"),
        tagged(rings, "ring_sensitivity"),
        tagged(regions, "regional_heterogeneity"),
        tagged(periods, "period_heterogeneity"),
    ])


def table_s8() -> None:
    concurrence = pd.read_csv(SOURCE / "corrected_inversion_concurrence_summary.csv")
    nulls = pd.read_csv(SOURCE / "severe_inversion_timing_null_summary.csv")
    write("S8", [tagged(concurrence, "concurrence"), tagged(nulls, "timing_nulls")])


def main() -> None:
    table_s1()
    table_s2()
    table_s3()
    table_s4()
    table_s5()
    table_s6()
    table_s7()
    table_s8()
    print(f"Supplementary table sources written to {OUTPUT}")


if __name__ == "__main__":
    main()
