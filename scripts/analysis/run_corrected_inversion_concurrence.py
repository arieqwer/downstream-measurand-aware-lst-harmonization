from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/external/valid_city_interval_panel.parquet"
OUT = ROOT / "data/processed/analysis_outputs"
THRESHOLDS = [0.0, 0.1, 0.25, 0.5]


def main() -> None:
    columns = [
        "uc_id",
        "year",
        "step8",
        "time_id",
        "dhd",
        "high_green",
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
    rows = []
    interval_rows = []
    for threshold in THRESHOLDS:
        event = (
            frame["dhd"].eq(1)
            & frame["heat_true_night_t2m_local_p90"].eq(1)
            & frame["day_anomaly_contrast"].lt(-threshold)
            & frame["night_anomaly_contrast"].gt(threshold)
        )
        concurrent = (
            frame[event]
            .groupby(["year", "step8", "time_id"], as_index=False)
            .agg(
                concurrent_represented_population=("population_2025", "sum"),
                concurrent_cities=("uc_id", "nunique"),
            )
        )
        concurrent["inversion_threshold_c"] = threshold
        interval_rows.append(concurrent)
        maximum = concurrent.loc[concurrent["concurrent_represented_population"].idxmax()]
        recent = concurrent[concurrent["year"].between(2021, 2025)]
        rows.append(
            {
                "inversion_threshold_c": threshold,
                "n_event_city_intervals": int(event.sum()),
                "n_cities_ever": frame.loc[event, "uc_id"].nunique(),
                "maximum_concurrent_represented_population": maximum[
                    "concurrent_represented_population"
                ],
                "maximum_year": int(maximum["year"]),
                "maximum_step8": int(maximum["step8"]),
                "maximum_concurrent_cities": int(maximum["concurrent_cities"]),
                "mean_concurrent_represented_population_2021_2025": recent[
                    "concurrent_represented_population"
                ].mean(),
                "maximum_concurrent_represented_population_2021_2025": recent[
                    "concurrent_represented_population"
                ].max(),
            }
        )
    summary = pd.DataFrame(rows)
    intervals = pd.concat(interval_rows, ignore_index=True)
    summary.to_csv(OUT / "corrected_inversion_concurrence_summary.csv", index=False)
    intervals.to_csv(OUT / "corrected_inversion_concurrence_intervals.csv", index=False)
    print(summary.assign(**{
        "maximum_million": summary["maximum_concurrent_represented_population"] / 1e6,
        "recent_mean_million": summary["mean_concurrent_represented_population_2021_2025"] / 1e6,
    }).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
