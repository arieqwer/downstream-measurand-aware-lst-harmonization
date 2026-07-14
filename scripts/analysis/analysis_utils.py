from math import erfc, sqrt

import numpy as np
import pandas as pd


def normal_two_sided_p(t_stat: np.ndarray) -> np.ndarray:
    return np.vectorize(lambda value: erfc(abs(float(value)) / sqrt(2.0)))(t_stat)


def twfe_cluster_ols(
    frame: pd.DataFrame,
    outcome: str,
    predictors: list[str],
    entity: str = "uc_id",
    time: str = "time_id",
    cluster: str = "uc_id",
    model_name: str = "twfe",
    max_iter: int = 12,
) -> pd.DataFrame:
    needed = list(dict.fromkeys([outcome, *predictors, entity, time, cluster]))
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

    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    residual = y - x @ beta
    xtx_inverse = np.linalg.pinv(x.T @ x)

    cluster_values = data[cluster].to_numpy()
    order = np.argsort(cluster_values)
    cluster_values = cluster_values[order]
    x_ordered = x[order]
    residual_ordered = residual[order]
    meat = np.zeros((x.shape[1], x.shape[1]))
    boundaries = np.r_[0, np.flatnonzero(cluster_values[1:] != cluster_values[:-1]) + 1, len(data)]
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        score = x_ordered[start:end].T @ residual_ordered[start:end]
        meat += np.outer(score, score)

    n_obs = len(data)
    n_clusters = data[cluster].nunique()
    n_terms = x.shape[1]
    finite_sample = (n_clusters / max(n_clusters - 1, 1)) * (
        (n_obs - 1) / max(n_obs - n_terms, 1)
    )
    covariance = finite_sample * xtx_inverse @ meat @ xtx_inverse
    standard_error = np.sqrt(np.clip(np.diag(covariance), 0, np.inf))
    t_stat = beta / standard_error

    return pd.DataFrame(
        {
            "model": model_name,
            "outcome": outcome,
            "term": terms,
            "estimate": beta,
            "std_error_cluster_city": standard_error,
            "ci95_low": beta - 1.96 * standard_error,
            "ci95_high": beta + 1.96 * standard_error,
            "t_stat": t_stat,
            "p_value": normal_two_sided_p(t_stat),
            "n_obs": n_obs,
            "n_cities": data[entity].nunique(),
            "n_times": data[time].nunique(),
        }
    )


def bootstrap_mean_ci(values: np.ndarray, random: np.random.Generator, draws: int = 2000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return np.nan, np.nan
    estimates = np.empty(draws)
    for index in range(draws):
        estimates[index] = random.choice(values, size=len(values), replace=True).mean()
    return tuple(np.quantile(estimates, [0.025, 0.975]))


def holm_adjust(p_values: pd.Series) -> pd.Series:
    p = p_values.to_numpy(dtype=float)
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    running = 0.0
    m = len(p)
    for rank, index in enumerate(order):
        candidate = min(1.0, (m - rank) * p[index])
        running = max(running, candidate)
        adjusted[index] = running
    return pd.Series(adjusted, index=p_values.index)
