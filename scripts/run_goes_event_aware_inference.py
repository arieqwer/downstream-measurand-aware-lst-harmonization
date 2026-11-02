from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS
from scipy import stats
from scipy.interpolate import PchipInterpolator
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.stats.sandwich_covariance import cov_cluster, cov_cluster_2groups


SEED = 20260806


def group_demean(values: np.ndarray, codes: np.ndarray) -> np.ndarray:
    result = np.zeros_like(values, dtype=float)
    counts = np.bincount(codes)
    for column in range(values.shape[1]):
        sums = np.bincount(codes, weights=values[:, column])
        result[:, column] = values[:, column] - sums[codes] / counts[codes]
    return result


def two_way_demean(
    values: np.ndarray,
    entity_codes: np.ndarray,
    time_codes: np.ndarray,
    max_iter: int = 100,
) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    if result.ndim == 1:
        result = result[:, None]
    for _ in range(max_iter):
        previous = result.copy()
        result = group_demean(result, entity_codes)
        result = group_demean(result, time_codes)
        if np.max(np.abs(result - previous)) < 1e-12:
            break
    return result


def prepare_twfe(
    frame: pd.DataFrame,
    outcome: str,
    predictors: list[str],
    entity: str = "uc_id",
    time: str = "event_time_id",
) -> dict[str, object]:
    needed = [outcome, *predictors, entity, time]
    data = frame[needed].replace([np.inf, -np.inf], np.nan).dropna().copy()
    entity_codes = pd.factorize(data[entity], sort=True)[0]
    time_codes = pd.factorize(data[time], sort=True)[0]
    matrix = data[[outcome, *predictors]].to_numpy(dtype=float)
    residualized = two_way_demean(matrix, entity_codes, time_codes)
    y = residualized[:, 0]
    x = residualized[:, 1:]
    keep = np.var(x, axis=0) > 1e-14
    x = x[:, keep]
    terms = [term for term, flag in zip(predictors, keep) if flag]
    if not terms:
        raise ValueError("No predictor variation remains after fixed effects")
    return {
        "data": data,
        "y": y,
        "x": x,
        "terms": terms,
        "entity_codes": entity_codes,
        "time_codes": time_codes,
    }


def fit_twfe(
    frame: pd.DataFrame,
    outcome: str,
    predictors: list[str],
    model_name: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    prepared = prepare_twfe(frame, outcome, predictors)
    y = prepared["y"]
    x = prepared["x"]
    fitted = sm.OLS(y, x).fit()
    city_codes = prepared["entity_codes"]
    event_codes = prepared["time_codes"]
    covariance, _, _ = cov_cluster_2groups(
        fitted, city_codes, event_codes, use_correction=True
    )
    event_covariance = cov_cluster(fitted, event_codes, use_correction=True)
    two_way_se = np.sqrt(np.clip(np.diag(covariance), 0, np.inf))
    event_se = np.sqrt(np.clip(np.diag(event_covariance), 0, np.inf))
    degrees_freedom = max(len(np.unique(event_codes)) - 1, 1)
    critical = stats.t.ppf(0.975, degrees_freedom)
    rows = []
    for index, term in enumerate(prepared["terms"]):
        t_event = fitted.params[index] / event_se[index]
        rows.append(
            {
                "model": model_name,
                "outcome": outcome,
                "term": term,
                "estimate": fitted.params[index],
                "se_two_way": two_way_se[index],
                "ci95_two_way_low": fitted.params[index]
                - critical * two_way_se[index],
                "ci95_two_way_high": fitted.params[index]
                + critical * two_way_se[index],
                "se_interval_cluster": event_se[index],
                "t_interval_cluster": t_event,
                "p_interval_cluster_t": 2
                * stats.t.sf(abs(t_event), degrees_freedom),
                "n_obs": len(prepared["data"]),
                "n_cities": prepared["data"]["uc_id"].nunique(),
                "n_intervals": prepared["data"]["event_time_id"].nunique(),
                "df_interval": degrees_freedom,
            }
        )
    return pd.DataFrame(rows), prepared


def exact_wild_interval_test(
    frame: pd.DataFrame,
    outcome: str,
    predictors: list[str],
    focal_term: str,
) -> dict[str, float]:
    prepared = prepare_twfe(frame, outcome, predictors)
    y = prepared["y"]
    x = prepared["x"]
    terms = prepared["terms"]
    focal_index = terms.index(focal_term)
    city_codes = prepared["entity_codes"]
    event_codes = prepared["time_codes"]
    unique_events = np.unique(event_codes)

    full_fit = sm.OLS(y, x).fit()
    event_covariance = cov_cluster(full_fit, event_codes, use_correction=True)
    event_se = np.sqrt(np.clip(np.diag(event_covariance), 0, np.inf))
    observed_t = full_fit.params[focal_index] / event_se[focal_index]

    control_indices = [i for i in range(x.shape[1]) if i != focal_index]
    if control_indices:
        restricted_x = x[:, control_indices]
        restricted_fit = sm.OLS(y, restricted_x).fit()
        fitted_null = restricted_fit.fittedvalues
        residual_null = restricted_fit.resid
    else:
        fitted_null = np.zeros_like(y)
        residual_null = y.copy()

    if len(unique_events) <= 16:
        sign_patterns = itertools.product((-1.0, 1.0), repeat=len(unique_events))
        inference_type = "exact_rademacher_enumeration"
    else:
        random = np.random.default_rng(SEED)
        draws = 19_999
        sign_patterns = random.choice(
            (-1.0, 1.0), size=(draws, len(unique_events)), replace=True
        )
        inference_type = "seeded_rademacher_monte_carlo"

    bootstrap_t = []
    for signs in sign_patterns:
        weights = np.asarray(signs)[event_codes]
        y_star = fitted_null + residual_null * weights
        y_star = two_way_demean(y_star, city_codes, event_codes).ravel()
        fit_star = sm.OLS(y_star, x).fit()
        covariance_star = cov_cluster(fit_star, event_codes, use_correction=True)
        se_star = np.sqrt(np.clip(np.diag(covariance_star), 0, np.inf))
        if np.isfinite(se_star[focal_index]) and se_star[focal_index] > 0:
            bootstrap_t.append(fit_star.params[focal_index] / se_star[focal_index])
    bootstrap_t = np.asarray(bootstrap_t)
    exceedances = int(np.sum(np.abs(bootstrap_t) >= abs(observed_t)))
    if inference_type == "exact_rademacher_enumeration":
        p_value = float(exceedances / len(bootstrap_t))
    else:
        p_value = float((exceedances + 1) / (len(bootstrap_t) + 1))
    return {
        "estimate": float(full_fit.params[focal_index]),
        "observed_t_interval_cluster": float(observed_t),
        "wild_interval_p_two_sided": p_value,
        "n_sign_patterns": int(len(bootstrap_t)),
        "n_intervals": int(len(unique_events)),
        "n_cities": int(prepared["data"]["uc_id"].nunique()),
        "n_obs": int(len(prepared["data"])),
        "inference_type": inference_type,
    }


def event_specific_slopes(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event, group in frame.groupby("event_time_id", sort=True):
        data = group[
            ["transition_shift_k", "severity10", "t2m_true_night_c"]
        ].dropna()
        if len(data) < 15 or data["severity10"].std() < 0.2:
            continue
        x = sm.add_constant(data[["severity10"]])
        fit = sm.OLS(data["transition_shift_k"], x).fit(cov_type="HC1")
        adjusted_x = sm.add_constant(data[["severity10", "t2m_true_night_c"]])
        adjusted = sm.OLS(data["transition_shift_k"], adjusted_x).fit(
            cov_type="HC1"
        )
        first = group.iloc[0]
        rows.append(
            {
                "event_time_id": event,
                "year": int(first["event_year"]),
                "step8": int(first["event_step8"]),
                "n": len(data),
                "severity_estimate": fit.params["severity10"],
                "severity_se_hc1": fit.bse["severity10"],
                "severity_ci95_low": fit.conf_int().loc["severity10", 0],
                "severity_ci95_high": fit.conf_int().loc["severity10", 1],
                "heat_adjusted_estimate": adjusted.params["severity10"],
                "heat_adjusted_se_hc1": adjusted.bse["severity10"],
            }
        )
    return pd.DataFrame(rows)


def summarize_event_replication(events: pd.DataFrame) -> dict[str, float]:
    estimates = events["severity_estimate"].dropna().to_numpy()
    standard_errors = events.loc[
        events["severity_estimate"].notna(), "severity_se_hc1"
    ].to_numpy()
    n = len(estimates)
    mean = estimates.mean()
    sem = stats.sem(estimates)
    critical = stats.t.ppf(0.975, max(n - 1, 1))
    weights = 1.0 / np.square(standard_errors)
    fixed = np.sum(weights * estimates) / np.sum(weights)
    q_stat = np.sum(weights * np.square(estimates - fixed))
    c_value = np.sum(weights) - np.sum(np.square(weights)) / np.sum(weights)
    tau2 = max(0.0, (q_stat - (n - 1)) / c_value) if c_value > 0 else 0.0
    random_weights = 1.0 / (np.square(standard_errors) + tau2)
    random_mean = np.sum(random_weights * estimates) / np.sum(random_weights)
    random_se = np.sqrt(1.0 / np.sum(random_weights))
    sign_test = stats.binomtest(
        int(np.sum(estimates > 0)), n=n, p=0.5, alternative="two-sided"
    )
    return {
        "n_intervals": n,
        "n_positive": int(np.sum(estimates > 0)),
        "equal_weight_mean": float(mean),
        "equal_weight_ci95_low": float(mean - critical * sem),
        "equal_weight_ci95_high": float(mean + critical * sem),
        "equal_weight_t_p": float(
            2 * stats.t.sf(abs(mean / sem), n - 1)
        ),
        "sign_test_p": float(sign_test.pvalue),
        "random_effects_mean": float(random_mean),
        "random_effects_ci95_low": float(random_mean - 1.96 * random_se),
        "random_effects_ci95_high": float(random_mean + 1.96 * random_se),
        "tau2": float(tau2),
    }


def leave_one_interval_out(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event in sorted(frame["event_time_id"].unique()):
        model, _ = fit_twfe(
            frame[frame["event_time_id"].ne(event)],
            "transition_shift_k",
            ["severity10"],
            f"leave_out_{event}",
        )
        row = model.iloc[0].to_dict()
        row["excluded_interval"] = event
        rows.append(row)
    return pd.DataFrame(rows)


def first_zero_crossing(hours: np.ndarray, values: np.ndarray) -> float:
    valid = np.isfinite(hours) & np.isfinite(values)
    if valid.sum() < 4:
        return np.nan
    x = hours[valid]
    y = values[valid]
    order = np.argsort(x)
    x = x[order]
    y = y[order]
    grid = np.linspace(x.min(), x.max(), 1801)
    curve = PchipInterpolator(x, y)(grid)
    indices = np.where((curve[:-1] <= 0) & (curve[1:] > 0))[0]
    if len(indices) == 0:
        return np.nan
    return float(grid[indices[0] + 1])


def hourly_twfe_curve(hourly: pd.DataFrame) -> pd.DataFrame:
    data = hourly[
        hourly["qa"].eq("strict")
        & hourly["valid"]
        & hourly["true_night_heat"]
        & (hourly["severe_hot"] | hourly["lower_severity_hot"])
    ].copy()
    data["severe_indicator"] = data["severe_hot"].astype(float)
    collapsed = (
        data.groupby(
            ["uc_id", "event_time_id", "target_hour_from_sunset"],
            observed=True,
        )
        .agg(
            core_ring_anomaly_k=("core_ring_anomaly_k", "mean"),
            severe_indicator=("severe_indicator", "first"),
        )
        .reset_index()
    )
    rows = []
    for hour, group in collapsed.groupby("target_hour_from_sunset", sort=True):
        if group["event_time_id"].nunique() < 2:
            continue
        try:
            model, _ = fit_twfe(
                group,
                "core_ring_anomaly_k",
                ["severe_indicator"],
                f"hour_{hour}",
            )
        except ValueError:
            continue
        row = model.iloc[0].to_dict()
        row["target_hour_from_sunset"] = hour
        rows.append(row)
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result = result.sort_values("target_hour_from_sunset")
    result["estimated_crossover_hour"] = first_zero_crossing(
        result["target_hour_from_sunset"].to_numpy(dtype=float),
        result["estimate"].to_numpy(dtype=float),
    )
    return result


def coverage_outputs(hourly: pd.DataFrame, city_event: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    strict = hourly[hourly["qa"].eq("strict")].copy()
    strict["severity_state"] = np.select(
        [strict["severe_hot"], strict["lower_severity_hot"]],
        ["severe", "lower_severity"],
        default="intermediate",
    )
    coverage_curve = (
        strict[strict["true_night_heat"]]
        .groupby(["severity_state", "target_hour_from_sunset"], observed=True)
        .agg(
            valid_fraction=("valid", "mean"),
            n_scans=("valid", "size"),
            n_cities=("uc_id", "nunique"),
            n_intervals=("event_time_id", "nunique"),
        )
        .reset_index()
    )
    availability = city_event[
        city_event["qa"].eq("strict") & city_event["true_night_heat"]
    ].copy()
    availability["transition_available"] = availability["n_transition_days"].ge(2).astype(float)
    availability["severity10"] = availability["hydroclimatic_severity"] / 10.0
    model, _ = fit_twfe(
        availability,
        "transition_available",
        ["severity10"],
        "clear_sky_transition_availability",
    )
    return coverage_curve, model


def inverse_probability_sensitivity(
    city_event: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    availability = city_event[
        city_event["qa"].eq("strict") & city_event["true_night_heat"]
    ].copy()
    availability["transition_available"] = availability["n_transition_days"].ge(2)
    availability["severity10"] = availability["hydroclimatic_severity"] / 10.0
    numeric = [
        column
        for column in [
            "severity10",
            "t2m_true_night_c",
            "z_water",
            "z_built",
        ]
        if column in availability.columns and availability[column].notna().any()
    ]
    categorical = ["uc_id", "event_time_id"]
    model_data = availability[
        ["transition_available", *numeric, *categorical]
    ].dropna()
    transformer = ColumnTransformer(
        [
            ("numeric", StandardScaler(), numeric),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical,
            ),
        ]
    )
    propensity_model = make_pipeline(
        transformer,
        LogisticRegression(C=1.0, max_iter=3000, solver="lbfgs"),
    )
    propensity_model.fit(
        model_data[numeric + categorical],
        model_data["transition_available"].astype(int),
    )
    probability = propensity_model.predict_proba(
        model_data[numeric + categorical]
    )[:, 1]
    model_data = model_data.copy()
    model_data["observation_probability"] = np.clip(probability, 0.05, 0.98)
    model_data["stabilized_ipw"] = (
        model_data["transition_available"].mean()
        / model_data["observation_probability"]
    )
    cap = model_data.loc[
        model_data["transition_available"], "stabilized_ipw"
    ].quantile(0.99)
    model_data["stabilized_ipw_capped"] = model_data["stabilized_ipw"].clip(
        upper=cap
    )

    analysis = availability.merge(
        model_data[
            [
                "uc_id",
                "event_time_id",
                "observation_probability",
                "stabilized_ipw_capped",
            ]
        ],
        on=["uc_id", "event_time_id"],
        how="inner",
        validate="one_to_one",
    )
    analysis = analysis[analysis["transition_available"]].dropna(
        subset=["transition_shift_k", "severity10", "stabilized_ipw_capped"]
    )
    panel = analysis.set_index(["uc_id", "event_time_id"])
    fitted = PanelOLS(
        panel["transition_shift_k"],
        panel[["severity10"]],
        weights=panel["stabilized_ipw_capped"],
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
    ).fit(
        cov_type="clustered",
        cluster_entity=True,
        cluster_time=True,
        debiased=True,
    )
    coefficient = pd.DataFrame(
        [
            {
                "model": "inverse_probability_weighted",
                "term": "severity10",
                "estimate": fitted.params["severity10"],
                "std_error_two_way_cluster": fitted.std_errors["severity10"],
                "ci95_low": fitted.conf_int().loc["severity10", "lower"],
                "ci95_high": fitted.conf_int().loc["severity10", "upper"],
                "p_value": fitted.pvalues["severity10"],
                "n_obs": int(fitted.nobs),
                "n_cities": int(analysis["uc_id"].nunique()),
                "n_intervals": int(analysis["event_time_id"].nunique()),
            }
        ]
    )
    diagnostics = pd.DataFrame(
        [
            {
                "availability_rate": model_data["transition_available"].mean(),
                "propensity_auc_in_sample": roc_auc_score(
                    model_data["transition_available"], probability
                ),
                "probability_min": probability.min(),
                "probability_median": np.median(probability),
                "probability_max": probability.max(),
                "ipw_99pct_cap": cap,
                "effective_sample_size": (
                    analysis["stabilized_ipw_capped"].sum() ** 2
                    / np.square(analysis["stabilized_ipw_capped"]).sum()
                ),
            }
        ]
    )
    return coefficient, diagnostics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--events-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--restrict-events-file", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    city_event = pd.read_parquet(
        args.analysis_dir / "goes_sunset_city_event_metrics.parquet"
    )
    hourly = pd.read_parquet(args.analysis_dir / "goes_sunset_hourly_analysis.parquet")
    events = pd.read_csv(args.events_file, dtype={"uc_id": str}).rename(
        columns={"year": "event_year", "step8": "event_step8", "time_id": "event_time_id"}
    )
    event_extra = [
        "uc_id",
        "event_year",
        "event_step8",
        "event_time_id",
        "t2m_true_night_c",
        "rzsm_pct",
        "vpd_pct",
        "pr_sum",
    ]
    event_extra = [column for column in event_extra if column in events.columns]
    city_event["uc_id"] = city_event["uc_id"].astype(str)
    merge_keys = ["uc_id", "event_year", "event_step8", "event_time_id"]
    city_event = city_event.merge(
        events[event_extra], on=merge_keys, how="left", validate="many_to_one"
    )
    city_event["severity10"] = city_event["hydroclimatic_severity"] / 10.0
    if "pr_sum" in city_event:
        city_event["log1p_pr_sum"] = np.log1p(city_event["pr_sum"].clip(lower=0))

    hourly["uc_id"] = hourly["uc_id"].astype(str)
    hourly_extra = [column for column in event_extra if column not in merge_keys]
    hourly = hourly.merge(
        events[merge_keys + hourly_extra],
        on=merge_keys,
        how="left",
        validate="many_to_one",
        suffixes=("", "_event"),
    )

    if args.restrict_events_file is not None:
        restriction = pd.read_csv(args.restrict_events_file)
        event_column = "time_id" if "time_id" in restriction else "event_time_id"
        retained_events = set(restriction[event_column].dropna().astype(int))
        city_event = city_event[city_event["event_time_id"].isin(retained_events)]
        hourly = hourly[hourly["event_time_id"].isin(retained_events)]

    pre = hourly[
        hourly["qa"].eq("strict")
        & hourly["valid"]
        & hourly["target_hour_from_sunset"].between(-3, -1)
    ]
    pre = (
        pre.groupby(["uc_id", "event_time_id"], observed=True)
        .agg(
            pre_core_lst_k=("core_lst_k", "mean"),
            pre_ring_lst_k=("ring_lst_k", "mean"),
        )
        .reset_index()
    )
    pre["pre_mean_lst_c"] = (
        (pre["pre_core_lst_k"] + pre["pre_ring_lst_k"]) / 2.0 - 273.15
    )
    city_event = city_event.merge(
        pre[["uc_id", "event_time_id", "pre_mean_lst_c"]],
        on=["uc_id", "event_time_id"],
        how="left",
        validate="many_to_one",
    )

    primary = city_event[
        city_event["qa"].eq("strict")
        & city_event["true_night_heat"]
        & city_event["n_transition_days"].ge(2)
    ].copy()

    model_rows = []
    primary_model, _ = fit_twfe(
        primary, "transition_shift_k", ["severity10"], "primary"
    )
    model_rows.append(primary_model)
    high_coverage, _ = fit_twfe(
        primary[primary["n_transition_days"].ge(4)],
        "transition_shift_k",
        ["severity10"],
        "high_coverage",
    )
    model_rows.append(high_coverage)
    if (primary["n_transition_days"] >= 6).sum() >= 100:
        near_complete, _ = fit_twfe(
            primary[primary["n_transition_days"].ge(6)],
            "transition_shift_k",
            ["severity10"],
            "near_complete_six_days",
        )
        model_rows.append(near_complete)

    heat_predictors = ["severity10", "t2m_true_night_c", "pre_mean_lst_c"]
    if "log1p_pr_sum" in primary:
        heat_predictors.append("log1p_pr_sum")
    adjusted, _ = fit_twfe(
        primary,
        "transition_shift_k",
        heat_predictors,
        "heat_initial_state_adjusted",
    )
    model_rows.append(adjusted)

    component = primary.copy()
    component["soil_dryness10"] = (100.0 - component["rzsm_pct"]) / 10.0
    component["vpd10"] = component["vpd_pct"] / 10.0
    component_model, _ = fit_twfe(
        component,
        "transition_shift_k",
        ["soil_dryness10", "vpd10", "t2m_true_night_c", "pre_mean_lst_c"],
        "hydroclimate_components_adjusted",
    )
    model_rows.append(component_model)
    models = pd.concat(model_rows, ignore_index=True)

    wild_primary = exact_wild_interval_test(
        primary, "transition_shift_k", ["severity10"], "severity10"
    )
    wild_adjusted = exact_wild_interval_test(
        primary,
        "transition_shift_k",
        heat_predictors,
        "severity10",
    )
    wild = pd.DataFrame(
        [
            {"model": "primary", **wild_primary},
            {"model": "heat_initial_state_adjusted", **wild_adjusted},
        ]
    )

    event_slopes = event_specific_slopes(primary)
    event_summary = summarize_event_replication(event_slopes)
    loo = leave_one_interval_out(primary)
    hourly_curve = hourly_twfe_curve(hourly)
    coverage_curve, coverage_model = coverage_outputs(hourly, city_event)
    ipw_model, ipw_diagnostics = inverse_probability_sensitivity(city_event)

    models.to_csv(args.output_dir / "event_aware_twfe.csv", index=False)
    wild.to_csv(args.output_dir / "exact_wild_interval_tests.csv", index=False)
    event_slopes.to_csv(args.output_dir / "event_specific_slopes.csv", index=False)
    loo.to_csv(args.output_dir / "leave_one_interval_out.csv", index=False)
    hourly_curve.to_csv(args.output_dir / "formal_hourly_crossover_curve.csv", index=False)
    coverage_curve.to_csv(args.output_dir / "clear_sky_coverage_by_hour.csv", index=False)
    coverage_model.to_csv(args.output_dir / "clear_sky_availability_model.csv", index=False)
    ipw_model.to_csv(args.output_dir / "inverse_probability_weighted_model.csv", index=False)
    ipw_diagnostics.to_csv(
        args.output_dir / "inverse_probability_weight_diagnostics.csv", index=False
    )
    with (args.output_dir / "event_replication_summary.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump({"label": args.label, **event_summary}, stream, indent=2)

    report = {
        "label": args.label,
        "primary": wild_primary,
        "adjusted": wild_adjusted,
        "event_replication": event_summary,
        "crossover_hour": (
            float(hourly_curve["estimated_crossover_hour"].iloc[0])
            if not hourly_curve.empty
            else float("nan")
        ),
        "leave_one_interval_min": float(
            loo.loc[loo["term"].eq("severity10"), "estimate"].min()
        ),
        "leave_one_interval_max": float(
            loo.loc[loo["term"].eq("severity10"), "estimate"].max()
        ),
        "ipw_estimate": float(ipw_model["estimate"].iloc[0]),
        "ipw_ci95_low": float(ipw_model["ci95_low"].iloc[0]),
        "ipw_ci95_high": float(ipw_model["ci95_high"].iloc[0]),
    }
    with (args.output_dir / "event_aware_inference_report.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
