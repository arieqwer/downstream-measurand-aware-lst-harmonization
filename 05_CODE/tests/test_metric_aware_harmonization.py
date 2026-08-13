from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from metric_aware_harmonization import (  # noqa: E402
    certify_direction,
    linear_metric_budget,
    one_standard_error_choice,
)


class MetricAwareHarmonizationTests(unittest.TestCase):
    def test_linear_metric_identity_closes(self) -> None:
        rng = np.random.default_rng(17)
        raw = rng.normal(size=(2000, 3)) @ np.array(
            [[1.0, 0.4, 0.2], [0.0, 0.8, 0.3], [0.0, 0.0, 0.6]]
        )
        harmonized = 0.7 * raw + rng.normal(scale=0.15, size=raw.shape)
        result = linear_metric_budget(raw, harmonized, np.array([1.0, -1.0, 0.5]))
        self.assertLess(abs(result.closure_residual), 1e-12)
        self.assertAlmostEqual(
            result.raw_metric_mse,
            result.raw_metric_variance + result.raw_metric_bias_squared,
            places=12,
        )

    def test_component_improvement_can_worsen_difference(self) -> None:
        rng = np.random.default_rng(23)
        common = rng.normal(scale=1.0, size=50_000)
        raw = np.column_stack(
            [
                common + rng.normal(scale=0.10, size=len(common)),
                common + rng.normal(scale=0.10, size=len(common)),
            ]
        )
        harmonized = rng.normal(scale=0.55, size=(len(common), 2))
        self.assertTrue(
            np.sqrt(np.mean(harmonized**2, axis=0)).max()
            < np.sqrt(np.mean(raw**2, axis=0)).min()
        )
        result = linear_metric_budget(raw, harmonized, np.array([1.0, -1.0]))
        self.assertLess(result.net_metric_mse_gain, 0)

    def test_one_standard_error_rule_can_retain_raw(self) -> None:
        choice = one_standard_error_choice(
            {
                "raw": (0.640, 0.030),
                "component": (0.625, 0.025),
                "direct": (0.620, 0.028),
            },
            ["raw", "component", "direct"],
        )
        self.assertEqual(choice, "raw")

    def test_direction_gate_abstains_when_zero_is_in_interval(self) -> None:
        result = certify_direction(
            np.array([0.1, -0.8, -0.2]), np.array([0.9, -0.1, 0.4])
        )
        np.testing.assert_array_equal(result, np.array([1, -1, 0]))


if __name__ == "__main__":
    unittest.main()
