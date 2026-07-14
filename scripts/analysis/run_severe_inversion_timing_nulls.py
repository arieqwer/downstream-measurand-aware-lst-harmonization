from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/external/valid_city_interval_panel.parquet"
OUT = ROOT / "data/processed/analysis_outputs"
RANDOM_SEED = 20260714
N_SIMULATIONS = 500
N_STEPS = 46
INVERSION_THRESHOLD_C = 0.25


def slope(years: np.ndarray, values: np.ndarray) -> float:
    x = years.astype(float)
    x -= x.mean()
    return float(np.dot(x, values - values.mean()) / np.dot(x, x))


def annual_statistics(city_counts: np.ndarray, population: np.ndarray, years: np.ndarray) -> dict:
    max_city = city_counts.max(axis=1)
    p90_city = np.quantile(city_counts, 0.90, axis=1)
    max_population = population.max(axis=1)
    return {
        "max_city_count": slope(years, max_city),
        "p90_city_count": slope(years, p90_city),
        "max_population": slope(years, max_population),
    }


def summarize(observed: dict, draws: pd.DataFrame, null_name: str) -> pd.DataFrame:
    rows = []
    for statistic, observed_value in observed.items():
        values = draws.loc[draws["statistic"].eq(statistic), "slope"].to_numpy(float)
        rows.append(
            {
                "null_name": null_name,
                "statistic": statistic,
                "observed_slope": observed_value,
                "null_mean_slope": values.mean(),
                "null_ci95_low": np.quantile(values, 0.025),
                "null_ci95_high": np.quantile(values, 0.975),
                "empirical_p_one_sided": (np.sum(values >= observed_value) + 1) / (len(values) + 1),
                "n_simulations": len(values),
            }
        )
    return pd.DataFrame(rows)


def prepare() -> tuple[pd.DataFrame, np.ndarray]:
    columns = [
        "uc_id",
        "year",
        "step8",
        "dhd",
        "high_green",
        "un_sdg_reg",
        "population_2025",
        "heat_true_night_t2m_local_p90",
        "core_tb_day_anom",
        "ring_tb_day_anom",
        "core_tb_night_anom",
        "ring_tb_night_anom",
    ]
    frame = pd.read_parquet(PANEL, columns=columns)
    frame = frame[frame["high_green"].eq(1)].copy()
    frame["day_anomaly_contrast"] = frame["core_tb_day_anom"] - frame["ring_tb_day_anom"]
    frame["night_anomaly_contrast"] = frame["core_tb_night_anom"] - frame["ring_tb_night_anom"]
    frame["eligible"] = frame["dhd"].eq(1) & frame["heat_true_night_t2m_local_p90"].eq(1)
    frame["event"] = (
        frame["eligible"]
        & frame["day_anomaly_contrast"].lt(-INVERSION_THRESHOLD_C)
        & frame["night_anomaly_contrast"].gt(INVERSION_THRESHOLD_C)
    )
    years = np.array(sorted(frame["year"].unique()), dtype=int)
    return frame, years


def observed_arrays(frame: pd.DataFrame, years: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    year_index = {year: index for index, year in enumerate(years)}
    count = np.zeros((len(years), N_STEPS), dtype=float)
    population = np.zeros((len(years), N_STEPS), dtype=float)
    event = frame[frame["event"]].copy()
    for row in event.itertuples(index=False):
        yi = year_index[int(row.year)]
        si = int(row.step8) - 1
        count[yi, si] += 1
        population[yi, si] += float(row.population_2025)
    return count, population


def city_shift_null(
    frame: pd.DataFrame, years: np.ndarray, random: np.random.Generator
) -> pd.DataFrame:
    year_index = {year: index for index, year in enumerate(years)}
    groups = []
    for (_, year), subset in frame[frame["event"]].groupby(["uc_id", "year"], sort=False):
        vector = np.zeros(N_STEPS, dtype=float)
        vector[subset["step8"].astype(int).to_numpy() - 1] = 1
        groups.append((year_index[int(year)], vector, float(subset["population_2025"].iloc[0])))
    rows = []
    for simulation in range(N_SIMULATIONS):
        count = np.zeros((len(years), N_STEPS), dtype=float)
        population = np.zeros_like(count)
        for yi, vector, weight in groups:
            shifted = np.roll(vector, int(random.integers(0, N_STEPS)))
            count[yi] += shifted
            population[yi] += shifted * weight
        for statistic, value in annual_statistics(count, population, years).items():
            rows.append({"simulation": simulation, "statistic": statistic, "slope": value})
    return pd.DataFrame(rows)


def region_block_null(
    frame: pd.DataFrame, years: np.ndarray, random: np.random.Generator
) -> pd.DataFrame:
    year_index = {year: index for index, year in enumerate(years)}
    blocks = []
    for (_, year), subset in frame[frame["event"]].groupby(["un_sdg_reg", "year"], sort=False):
        count = np.zeros(N_STEPS, dtype=float)
        population = np.zeros(N_STEPS, dtype=float)
        for row in subset.itertuples(index=False):
            step = int(row.step8) - 1
            count[step] += 1
            population[step] += float(row.population_2025)
        blocks.append((year_index[int(year)], count, population))
    rows = []
    for simulation in range(N_SIMULATIONS):
        count = np.zeros((len(years), N_STEPS), dtype=float)
        population = np.zeros_like(count)
        for yi, block_count, block_population in blocks:
            shift = int(random.integers(0, N_STEPS))
            count[yi] += np.roll(block_count, shift)
            population[yi] += np.roll(block_population, shift)
        for statistic, value in annual_statistics(count, population, years).items():
            rows.append({"simulation": simulation, "statistic": statistic, "slope": value})
    return pd.DataFrame(rows)


def exposure_preserving_null(
    frame: pd.DataFrame, years: np.ndarray, random: np.random.Generator
) -> pd.DataFrame:
    year_index = {year: index for index, year in enumerate(years)}
    groups = []
    for (_, year), subset in frame.groupby(["uc_id", "year"], sort=False):
        eligible = np.unique(subset.loc[subset["eligible"], "step8"].astype(int).to_numpy() - 1)
        k = int(subset["event"].sum())
        if k > 0 and len(eligible) >= k:
            groups.append((year_index[int(year)], eligible, k, float(subset["population_2025"].iloc[0])))
    rows = []
    for simulation in range(N_SIMULATIONS):
        count = np.zeros((len(years), N_STEPS), dtype=float)
        population = np.zeros_like(count)
        for yi, eligible, k, weight in groups:
            selected = random.choice(eligible, size=k, replace=False)
            np.add.at(count[yi], selected, 1)
            np.add.at(population[yi], selected, weight)
        for statistic, value in annual_statistics(count, population, years).items():
            rows.append({"simulation": simulation, "statistic": statistic, "slope": value})
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame, years = prepare()
    observed_count, observed_population = observed_arrays(frame, years)
    observed = annual_statistics(observed_count, observed_population, years)
    random = np.random.default_rng(RANDOM_SEED)
    nulls = [
        ("city-year circular shift", city_shift_null(frame, years, random)),
        ("region-year block shift", region_block_null(frame, years, random)),
        (
            "DHD and true-night-heat timing preserved",
            exposure_preserving_null(frame, years, random),
        ),
    ]
    summary = pd.concat(
        [summarize(observed, draws, name) for name, draws in nulls], ignore_index=True
    )
    draws = pd.concat(
        [draws.assign(null_name=name) for name, draws in nulls], ignore_index=True
    )
    summary.to_csv(OUT / "severe_inversion_timing_null_summary.csv", index=False)
    draws.to_csv(OUT / "severe_inversion_timing_null_draws.csv", index=False)
    print(summary.round(6).to_string(index=False))


if __name__ == "__main__":
    main()
