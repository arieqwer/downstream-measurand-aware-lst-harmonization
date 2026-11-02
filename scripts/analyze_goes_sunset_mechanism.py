from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups


ROOT = Path(__file__).resolve().parents[1]
from goes_analysis_utils import bootstrap_mean_ci, twfe_cluster_ols


DEFAULT_DATA = ROOT / "data/goes_sunset_pilot"
DEFAULT_OUT = ROOT / "outputs/goes_sunset_mechanism"
DATA = DEFAULT_DATA
OUT = DEFAULT_OUT
# Output created by the configured runner when needed.
RANDOM_SEED = 20260806


def twfe_two_way_cluster_ols(
    frame: pd.DataFrame,
    outcome: str,
    predictors: list[str],
    entity: str = "uc_id",
    time: str = "time_id",
    model_name: str = "twfe_two_way",
    max_iter: int = 12,
) -> pd.DataFrame:
    needed = list(dict.fromkeys([outcome, *predictors, entity, time]))
    data = frame[needed].replace([np.inf, -np.inf], np.nan).dropna().copy()
    work = data[[outcome, *predictors]].astype("float64")
    for _ in range(max_iter):
        previous = work.to_numpy(copy=True)
        work -= work.groupby(data[entity], sort=False).transform("mean")
        work -= work.groupby(data[time], sort=False).transform("mean")
        if np.nanmax(np.abs(work.to_numpy() - previous)) < 1e-10:
            break

    y = work[outcome].to_numpy(dtype=float)
    x_all = work[predictors].to_numpy(dtype=float)
    keep = np.nanvar(x_all, axis=0) > 1e-14
    x = x_all[:, keep]
    terms = [term for term, flag in zip(predictors, keep) if flag]
    if not terms:
        return pd.DataFrame()
    fitted = sm.OLS(y, x).fit()
    city_groups = pd.factorize(data[entity], sort=True)[0]
    time_groups = pd.factorize(data[time], sort=True)[0]
    covariance, _, _ = cov_cluster_2groups(
        fitted, city_groups, time_groups, use_correction=True
    )
    standard_error = np.sqrt(np.clip(np.diag(covariance), 0, np.inf))
    valid_standard_error = np.isfinite(standard_error) & (standard_error > 0)
    t_stat = np.full_like(fitted.params, np.nan, dtype=float)
    t_stat[valid_standard_error] = (
        fitted.params[valid_standard_error] / standard_error[valid_standard_error]
    )
    n_city = data[entity].nunique()
    n_time = data[time].nunique()
    degrees_freedom = max(min(n_city, n_time) - 1, 1)
    critical = stats.t.ppf(0.975, degrees_freedom)
    p_value = np.full_like(t_stat, np.nan, dtype=float)
    p_value[valid_standard_error] = 2.0 * stats.t.sf(
        np.abs(t_stat[valid_standard_error]), degrees_freedom
    )
    ci95_low = np.full_like(fitted.params, np.nan, dtype=float)
    ci95_high = np.full_like(fitted.params, np.nan, dtype=float)
    ci95_low[valid_standard_error] = (
        fitted.params[valid_standard_error]
        - critical * standard_error[valid_standard_error]
    )
    ci95_high[valid_standard_error] = (
        fitted.params[valid_standard_error]
        + critical * standard_error[valid_standard_error]
    )
    return pd.DataFrame(
        {
            "model": model_name,
            "outcome": outcome,
            "term": terms,
            "estimate": fitted.params,
            "std_error_cluster_city_interval": standard_error,
            "ci95_low": ci95_low,
            "ci95_high": ci95_high,
            "t_stat": t_stat,
            "p_value": p_value,
            "n_obs": len(data),
            "n_cities": n_city,
            "n_times": n_time,
            "df_inference": degrees_freedom,
            "se_method": "city_interval_cluster",
        }
    )


def slope(
    hours: pd.Series,
    values: pd.Series,
    minimum: int = 4,
    minimum_span: float = 3.0,
) -> float:
    valid = hours.notna() & values.notna()
    if valid.sum() < minimum:
        return np.nan
    x = hours[valid].to_numpy(dtype=float)
    y = values[valid].to_numpy(dtype=float)
    if np.ptp(x) < minimum_span:
        return np.nan
    return float(np.polyfit(x, y, 1)[0])


def prepare_hourly(qa: str) -> pd.DataFrame:
    hourly = pd.read_parquet(DATA / "goes_sunset_hourly.parquet")
    events = pd.read_csv(DATA / "goes_sunset_city_events.csv", dtype={"uc_id": str})
    hourly["uc_id"] = hourly["uc_id"].astype(str)
    events = events.rename(
        columns={
            "year": "event_year",
            "step8": "event_step8",
            "time_id": "event_time_id",
        }
    )
    event_columns = [
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "hydroclimatic_severity",
        "t2m_true_night_pct_rank",
        "true_night_heat",
        "severe_hot",
        "lower_severity_hot",
        "mean_water_support_ratio",
        "heat_retention_score",
        "profile",
    ]
    frame = hourly.merge(
        events[event_columns],
        on=["uc_id", "event_year", "event_step8", "event_time_id"],
        how="inner",
        validate="many_to_one",
    )
    frame["core_lst_k"] = frame[f"core_{qa}_lst_k"]
    frame["ring_lst_k"] = frame[f"ring_{qa}_lst_k"]
    frame["valid"] = (
        frame[f"core_{qa}_count"].ge(3)
        & frame[f"ring_{qa}_count"].ge(10)
        & frame["core_lst_k"].between(180, 380)
        & frame["ring_lst_k"].between(180, 380)
    )
    frame.loc[~frame["valid"], ["core_lst_k", "ring_lst_k"]] = np.nan
    frame["core_ring_anomaly_k"] = frame["core_lst_k"] - frame["ring_lst_k"]
    frame["qa"] = qa
    return frame


def daily_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "qa",
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "local_date",
    ]
    rows: list[dict[str, object]] = []
    for key, group in frame.groupby(keys, observed=True, sort=False):
        post = group[group["target_hour_from_sunset"].between(0, 6)]
        pre = group[group["target_hour_from_sunset"].between(-3, -1)]
        early = group[group["target_hour_from_sunset"].between(0, 2)]
        late = group[group["target_hour_from_sunset"].between(4, 6)]
        core_slope = slope(post["actual_hour_from_sunset"], post["core_lst_k"])
        ring_slope = slope(post["actual_hour_from_sunset"], post["ring_lst_k"])
        anomaly_slope = slope(
            post["actual_hour_from_sunset"], post["core_ring_anomaly_k"]
        )
        pre_anomaly_slope = slope(
            pre["actual_hour_from_sunset"],
            pre["core_ring_anomaly_k"],
            minimum=3,
            minimum_span=1.5,
        )
        row = dict(zip(keys, key))
        row.update(
            {
                "core_cooling_slope_k_h": core_slope,
                "ring_cooling_slope_k_h": ring_slope,
                "core_minus_ring_cooling_slope_k_h": (
                    core_slope - ring_slope
                    if np.isfinite(core_slope) and np.isfinite(ring_slope)
                    else np.nan
                ),
                "anomaly_slope_k_h": anomaly_slope,
                "pre_sunset_anomaly_slope_k_h": pre_anomaly_slope,
                "pre_sunset_anomaly_k": pre["core_ring_anomaly_k"].mean(),
                "early_postsunset_anomaly_k": early["core_ring_anomaly_k"].mean(),
                "late_postsunset_anomaly_k": late["core_ring_anomaly_k"].mean(),
                "transition_shift_k": (
                    late["core_ring_anomaly_k"].mean()
                    - pre["core_ring_anomaly_k"].mean()
                ),
                "n_valid_post_hours": int(post["core_ring_anomaly_k"].notna().sum()),
                "n_valid_pre_hours": int(pre["core_ring_anomaly_k"].notna().sum()),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def city_event_metrics(daily: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    measures = [
        "core_cooling_slope_k_h",
        "ring_cooling_slope_k_h",
        "core_minus_ring_cooling_slope_k_h",
        "anomaly_slope_k_h",
        "pre_sunset_anomaly_slope_k_h",
        "pre_sunset_anomaly_k",
        "early_postsunset_anomaly_k",
        "late_postsunset_anomaly_k",
        "transition_shift_k",
    ]
    keys = ["qa", "uc_id", "event_year", "event_step8", "event_time_id"]
    averaged = daily.groupby(keys, observed=True)[measures].mean().reset_index()
    counts = (
        daily.groupby(keys, observed=True)
        .agg(
            n_slope_days=("core_minus_ring_cooling_slope_k_h", "count"),
            n_pre_slope_days=("pre_sunset_anomaly_slope_k_h", "count"),
            n_pre_days=("pre_sunset_anomaly_k", "count"),
            n_late_days=("late_postsunset_anomaly_k", "count"),
            n_transition_days=("transition_shift_k", "count"),
        )
        .reset_index()
    )
    result = averaged.merge(counts, on=keys, validate="one_to_one")
    event_columns = [
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "hydroclimatic_severity",
        "t2m_true_night_pct_rank",
        "true_night_heat",
        "severe_hot",
        "lower_severity_hot",
        "mean_water_support_ratio",
        "heat_retention_score",
        "profile",
    ]
    result = result.merge(
        events[event_columns],
        on=["uc_id", "event_year", "event_step8", "event_time_id"],
        how="inner",
        validate="many_to_one",
    )
    result["severity10"] = result["hydroclimatic_severity"] / 10.0
    result["z_water"] = (
        result["mean_water_support_ratio"]
        - result["mean_water_support_ratio"].mean()
    ) / result["mean_water_support_ratio"].std(ddof=0)
    result["z_built"] = (
        result["heat_retention_score"] - result["heat_retention_score"].mean()
    ) / result["heat_retention_score"].std(ddof=0)
    result["z_night_heat"] = (
        result["t2m_true_night_pct_rank"]
        - result["t2m_true_night_pct_rank"].mean()
    ) / result["t2m_true_night_pct_rank"].std(ddof=0)
    result["severity_x_water"] = result["severity10"] * result["z_water"]
    result["severity_x_built"] = result["severity10"] * result["z_built"]
    result["time_id"] = result["event_time_id"]
    return result


def fixed_effect_models(frame: pd.DataFrame) -> pd.DataFrame:
    outcomes = [
        "core_cooling_slope_k_h",
        "ring_cooling_slope_k_h",
        "core_minus_ring_cooling_slope_k_h",
        "pre_sunset_anomaly_slope_k_h",
        "late_postsunset_anomaly_k",
        "transition_shift_k",
        "pre_sunset_anomaly_k",
    ]
    predictors = [
        "severity10",
        "severity_x_water",
        "severity_x_built",
        "z_night_heat",
    ]
    outputs: list[pd.DataFrame] = []
    for qa in ["recommended", "strict"]:
        qa_frame = frame[frame["qa"].eq(qa)]
        for sample_name, sample, required_days in [
            ("all", qa_frame, 2),
            ("true_night_heat", qa_frame[qa_frame["true_night_heat"]], 2),
            (
                "true_night_heat_high_coverage",
                qa_frame[qa_frame["true_night_heat"]],
                4,
            ),
            (
                "discovery_2018_2021",
                qa_frame[qa_frame["event_year"].le(2021)],
                2,
            ),
            (
                "confirmation_2022_2024",
                qa_frame[qa_frame["event_year"].ge(2022)],
                2,
            ),
            (
                "hot_discovery_2018_2021",
                qa_frame[
                    qa_frame["true_night_heat"] & qa_frame["event_year"].le(2021)
                ],
                2,
            ),
            (
                "hot_confirmation_2022_2024",
                qa_frame[
                    qa_frame["true_night_heat"] & qa_frame["event_year"].ge(2022)
                ],
                2,
            ),
        ]:
            sample_predictors = [
                predictor
                for predictor in predictors
                if predictor in sample.columns
                and sample[predictor].notna().sum() >= 10
                and sample[predictor].dropna().var() > 1e-14
            ]
            if not sample_predictors:
                continue
            for outcome in outcomes:
                if outcome == "pre_sunset_anomaly_slope_k_h":
                    minimum_days = "n_pre_slope_days"
                elif "slope" in outcome:
                    minimum_days = "n_slope_days"
                elif outcome == "pre_sunset_anomaly_k":
                    minimum_days = "n_pre_days"
                elif outcome == "transition_shift_k":
                    minimum_days = "n_transition_days"
                else:
                    minimum_days = "n_late_days"
                analysis = sample[sample[minimum_days].ge(required_days)].copy()
                if (
                    len(analysis) < 10
                    or analysis["uc_id"].nunique() < 3
                    or analysis["time_id"].nunique() < 2
                ):
                    continue
                model = twfe_cluster_ols(
                    analysis,
                    outcome,
                    sample_predictors,
                    model_name=f"goes_{qa}_{sample_name}_{outcome}",
                )
                model["qa"] = qa
                model["sample"] = sample_name
                model["se_method"] = "city_cluster"
                outputs.append(model)
                two_way = twfe_two_way_cluster_ols(
                    analysis,
                    outcome,
                    sample_predictors,
                    model_name=f"goes_two_way_{qa}_{sample_name}_{outcome}",
                )
                two_way["qa"] = qa
                two_way["sample"] = sample_name
                outputs.append(two_way)
    return pd.concat(outputs, ignore_index=True)


def state_contrasts(frame: pd.DataFrame) -> pd.DataFrame:
    random = np.random.default_rng(RANDOM_SEED)
    rows: list[dict[str, object]] = []
    outcomes = [
        "core_cooling_slope_k_h",
        "ring_cooling_slope_k_h",
        "core_minus_ring_cooling_slope_k_h",
        "late_postsunset_anomaly_k",
        "transition_shift_k",
    ]
    for qa in ["recommended", "strict"]:
        data = frame[frame["qa"].eq(qa)].copy()
        periods = [("all", data)]
        if data["event_year"].min() <= 2021:
            periods.extend(
                [
                    ("discovery_2018_2021", data[data["event_year"].le(2021)]),
                    ("confirmation_2022_2024", data[data["event_year"].ge(2022)]),
                ]
            )
        for period, period_data in periods:
            for outcome in outcomes:
                minimum_days = {
                    "core_cooling_slope_k_h": "n_slope_days",
                    "ring_cooling_slope_k_h": "n_slope_days",
                    "core_minus_ring_cooling_slope_k_h": "n_slope_days",
                    "late_postsunset_anomaly_k": "n_late_days",
                    "transition_shift_k": "n_transition_days",
                }[outcome]
                city_state = (
                    period_data[
                        period_data["true_night_heat"]
                        & period_data[minimum_days].ge(2)
                    ]
                    .assign(
                        severity_state=lambda x: np.select(
                            [x["severe_hot"], x["lower_severity_hot"]],
                            ["severe", "lower severity"],
                            default="intermediate",
                        )
                    )
                    .loc[lambda x: x["severity_state"].ne("intermediate")]
                    .groupby(["uc_id", "severity_state"], observed=True)[outcome]
                    .mean()
                    .unstack("severity_state")
                )
                if not {"severe", "lower severity"}.issubset(city_state.columns):
                    continue
                city_state = city_state.dropna(subset=["severe", "lower severity"])
                differences = (
                    city_state["severe"] - city_state["lower severity"]
                ).dropna().to_numpy(dtype=float)
                low, high = bootstrap_mean_ci(differences, random, draws=5000)
                rows.append(
                    {
                        "qa": qa,
                        "period": period,
                        "outcome": outcome,
                        "n_paired_cities": len(differences),
                        "severe_minus_lower_severity": np.mean(differences)
                        if len(differences)
                        else np.nan,
                        "bootstrap_ci95_low": low,
                        "bootstrap_ci95_high": high,
                    }
                )
    return pd.DataFrame(rows)


def trajectory_summary(hourly: pd.DataFrame) -> pd.DataFrame:
    data = hourly[hourly["valid"] & hourly["true_night_heat"]].copy()
    data["severity_state"] = np.select(
        [data["severe_hot"], data["lower_severity_hot"]],
        ["severe", "lower severity"],
        default="intermediate",
    )
    data = data[data["severity_state"].ne("intermediate")]
    city_hour = (
        data.groupby(
            ["qa", "uc_id", "severity_state", "target_hour_from_sunset"],
            observed=True,
        )["core_ring_anomaly_k"]
        .mean()
        .reset_index()
    )
    return (
        city_hour.groupby(
            ["qa", "severity_state", "target_hour_from_sunset"], observed=True
        )
        .agg(
            n_cities=("uc_id", "nunique"),
            mean_core_ring_anomaly_k=("core_ring_anomaly_k", "mean"),
            se_core_ring_anomaly_k=("core_ring_anomaly_k", "sem"),
        )
        .reset_index()
    )


def relative_temperature_trajectory(hourly: pd.DataFrame) -> pd.DataFrame:
    data = hourly[hourly["valid"] & hourly["true_night_heat"]].copy()
    data["severity_state"] = np.select(
        [data["severe_hot"], data["lower_severity_hot"]],
        ["severe", "lower severity"],
        default="intermediate",
    )
    data = data[data["severity_state"].ne("intermediate")]
    long = data.melt(
        id_vars=[
            "qa",
            "uc_id",
            "severity_state",
            "target_hour_from_sunset",
        ],
        value_vars=["core_lst_k", "ring_lst_k"],
        var_name="unit",
        value_name="lst_k",
    )
    city_hour = (
        long.groupby(
            [
                "qa",
                "uc_id",
                "severity_state",
                "unit",
                "target_hour_from_sunset",
            ],
            observed=True,
        )["lst_k"]
        .mean()
        .reset_index()
    )
    sunset = city_hour[city_hour["target_hour_from_sunset"].eq(0)][
        ["qa", "uc_id", "severity_state", "unit", "lst_k"]
    ].rename(columns={"lst_k": "sunset_lst_k"})
    city_hour = city_hour.merge(
        sunset,
        on=["qa", "uc_id", "severity_state", "unit"],
        how="inner",
        validate="many_to_one",
    )
    city_hour["change_from_sunset_k"] = city_hour["lst_k"] - city_hour[
        "sunset_lst_k"
    ]
    return (
        city_hour.groupby(
            ["qa", "severity_state", "unit", "target_hour_from_sunset"],
            observed=True,
        )
        .agg(
            n_cities=("uc_id", "nunique"),
            mean_change_from_sunset_k=("change_from_sunset_k", "mean"),
            se_change_from_sunset_k=("change_from_sunset_k", "sem"),
        )
        .reset_index()
    )


def main() -> None:
    global DATA, OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    DATA = args.data_dir.expanduser().resolve()
    OUT = args.output_dir.expanduser().resolve()
    # Output created by the configured runner when needed.

    events = pd.read_csv(DATA / "goes_sunset_city_events.csv", dtype={"uc_id": str})
    events = events.rename(
        columns={
            "year": "event_year",
            "step8": "event_step8",
            "time_id": "event_time_id",
        }
    )
    hourly_frames = [prepare_hourly(qa) for qa in ["recommended", "strict"]]
    hourly = pd.concat(hourly_frames, ignore_index=True)
    daily = daily_metrics(hourly)
    city_event = city_event_metrics(daily, events)
    models = fixed_effect_models(city_event)
    contrasts = state_contrasts(city_event)
    trajectories = trajectory_summary(hourly)
    relative_trajectories = relative_temperature_trajectory(hourly)

    hourly.to_parquet(OUT / "goes_sunset_hourly_analysis.parquet", index=False)
    daily.to_parquet(OUT / "goes_sunset_daily_metrics.parquet", index=False)
    city_event.to_parquet(OUT / "goes_sunset_city_event_metrics.parquet", index=False)
    models.to_csv(OUT / "goes_sunset_twfe.csv", index=False)
    contrasts.to_csv(OUT / "goes_sunset_paired_state_contrasts.csv", index=False)
    trajectories.to_csv(OUT / "goes_sunset_trajectory_summary.csv", index=False)
    relative_trajectories.to_csv(
        OUT / "goes_sunset_relative_temperature_trajectories.csv", index=False
    )

    focal_terms = models[
        models["term"].isin(["severity10", "severity_x_water", "severity_x_built"])
        & models["sample"].isin(
            [
                "true_night_heat",
                "hot_discovery_2018_2021",
                "hot_confirmation_2022_2024",
            ]
        )
    ]
    print(focal_terms.to_string(index=False))
    print("\nPaired state contrasts")
    print(contrasts.to_string(index=False))


if __name__ == "__main__":
    main()
