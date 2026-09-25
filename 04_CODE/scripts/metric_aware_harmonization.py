from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class LinearMetricBudget:
    raw_component_bias: list[float]
    harmonized_component_bias: list[float]
    raw_component_covariance: list[list[float]]
    harmonized_component_covariance: list[list[float]]
    raw_metric_variance: float
    harmonized_metric_variance: float
    raw_metric_bias_squared: float
    harmonized_metric_bias_squared: float
    raw_metric_mse: float
    harmonized_metric_mse: float
    metric_variance_gain: float
    metric_bias_gain: float
    net_metric_mse_gain: float
    closure_residual: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalized_weights(n: int, weights: np.ndarray | None) -> np.ndarray:
    if weights is None:
        return np.full(n, 1 / n, dtype=float)
    result = np.asarray(weights, dtype=float)
    if result.shape != (n,):
        raise ValueError(f"Expected {n} weights, received shape {result.shape}")
    if np.any(result < 0) or not np.isfinite(result).all() or result.sum() <= 0:
        raise ValueError("Weights must be finite, non-negative, and have positive sum")
    return result / result.sum()


def _moments(errors: np.ndarray, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    bias = np.sum(errors * weights[:, None], axis=0)
    centered = errors - bias
    covariance = (centered * weights[:, None]).T @ centered
    return bias, covariance


def linear_metric_budget(
    raw_component_errors: np.ndarray,
    harmonized_component_errors: np.ndarray,
    contrast: np.ndarray,
    weights: np.ndarray | None = None,
) -> LinearMetricBudget:
    """Propagate component errors to an arbitrary linear scientific measurand.

    The downstream metric error is ``contrast @ component_errors``. Population
    moments are used so the MSE identity closes exactly up to floating-point error.
    """

    raw = np.asarray(raw_component_errors, dtype=float)
    harmonized = np.asarray(harmonized_component_errors, dtype=float)
    contrast = np.asarray(contrast, dtype=float)
    if raw.ndim != 2 or harmonized.shape != raw.shape:
        raise ValueError("Raw and harmonized errors must be equally shaped 2-D arrays")
    if contrast.shape != (raw.shape[1],):
        raise ValueError("Contrast length must equal the number of components")
    if not np.isfinite(raw).all() or not np.isfinite(harmonized).all():
        raise ValueError("Component errors must be finite")
    normalized = _normalized_weights(len(raw), weights)
    raw_bias, raw_covariance = _moments(raw, normalized)
    harm_bias, harm_covariance = _moments(harmonized, normalized)

    raw_metric = raw @ contrast
    harm_metric = harmonized @ contrast
    raw_metric_variance = float(contrast @ raw_covariance @ contrast)
    harm_metric_variance = float(contrast @ harm_covariance @ contrast)
    raw_metric_bias_squared = float((contrast @ raw_bias) ** 2)
    harm_metric_bias_squared = float((contrast @ harm_bias) ** 2)
    raw_metric_mse = float(np.sum(normalized * raw_metric**2))
    harm_metric_mse = float(np.sum(normalized * harm_metric**2))
    variance_gain = raw_metric_variance - harm_metric_variance
    bias_gain = raw_metric_bias_squared - harm_metric_bias_squared
    net_gain = raw_metric_mse - harm_metric_mse
    return LinearMetricBudget(
        raw_component_bias=raw_bias.tolist(),
        harmonized_component_bias=harm_bias.tolist(),
        raw_component_covariance=raw_covariance.tolist(),
        harmonized_component_covariance=harm_covariance.tolist(),
        raw_metric_variance=raw_metric_variance,
        harmonized_metric_variance=harm_metric_variance,
        raw_metric_bias_squared=raw_metric_bias_squared,
        harmonized_metric_bias_squared=harm_metric_bias_squared,
        raw_metric_mse=raw_metric_mse,
        harmonized_metric_mse=harm_metric_mse,
        metric_variance_gain=variance_gain,
        metric_bias_gain=bias_gain,
        net_metric_mse_gain=net_gain,
        closure_residual=net_gain - variance_gain - bias_gain,
    )


def one_standard_error_choice(
    losses: Mapping[str, tuple[float, float]],
    conservative_preference: Sequence[str],
) -> str:
    """Select the most conservative candidate within one SE of the best loss."""

    if not losses:
        raise ValueError("At least one candidate loss is required")
    for name, (mean, standard_error) in losses.items():
        if not np.isfinite(mean) or not np.isfinite(standard_error):
            raise ValueError(f"Non-finite loss summary for {name}")
        if standard_error < 0:
            raise ValueError(f"Negative standard error for {name}")
    best = min(losses, key=lambda name: losses[name][0])
    threshold = losses[best][0] + losses[best][1]
    eligible = {name for name, (mean, _) in losses.items() if mean <= threshold}
    for name in conservative_preference:
        if name in eligible:
            return name
    return best


def certify_direction(lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    """Return +1, -1, or 0 when an interval supports, opposes, or spans zero."""

    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    if lower.shape != upper.shape:
        raise ValueError("Lower and upper bounds must have the same shape")
    if np.any(lower > upper):
        raise ValueError("Every lower bound must be no greater than its upper bound")
    return np.select([lower > 0, upper < 0], [1, -1], default=0).astype(int)
