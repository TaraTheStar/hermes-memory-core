import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from domain.core.anomaly_detector import ContextualAnomalyDetector
from domain.core.anomaly_config import MetricType, ThresholdProfile


class TestContextualAnomalyDetector(unittest.TestCase):
    def setUp(self):
        self.detector = ContextualAnomalyDetector()
        profile = ThresholdProfile(
            name="test_profile",
            thresholds={
                MetricType.COMMUNITY_SIZE: 10.0,
                MetricType.EDGE_WEIGHT: 0.1,
                MetricType.GRAPH_DENSITY: 0.8,
            },
            sensitivity_multiplier=1.0,
        )
        self.detector.register_profile("global", profile)

    def test_no_anomaly_below_threshold(self):
        result = self.detector.evaluate_metric(MetricType.COMMUNITY_SIZE, 5.0)
        self.assertIsNone(result)

    def test_anomaly_above_threshold(self):
        result = self.detector.evaluate_metric(MetricType.COMMUNITY_SIZE, 15.0)
        self.assertIsNotNone(result)
        self.assertEqual(result.pattern_type, "COMMUNITY_SIZE")

    def test_no_threshold_configured(self):
        result = self.detector.evaluate_metric(MetricType.NODE_DEGREE, 100.0)
        self.assertIsNone(result)

    def test_context_fallback_to_global(self):
        result = self.detector.evaluate_metric(
            MetricType.COMMUNITY_SIZE, 15.0, context_id="unknown_context"
        )
        self.assertIsNotNone(result)

    def test_custom_context_profile(self):
        strict_profile = ThresholdProfile(
            name="strict",
            thresholds={MetricType.COMMUNITY_SIZE: 3.0},
            sensitivity_multiplier=1.0,
        )
        self.detector.register_profile("strict_ctx", strict_profile)
        result = self.detector.evaluate_metric(
            MetricType.COMMUNITY_SIZE, 5.0, context_id="strict_ctx"
        )
        self.assertIsNotNone(result)

    def test_z_score_with_historical_values(self):
        # Value of 100 with history around 10 should be anomalous
        historical = [10.0, 11.0, 9.0, 10.5, 10.2]
        result = self.detector.evaluate_metric(
            MetricType.COMMUNITY_SIZE, 100.0, historical_values=historical
        )
        self.assertIsNotNone(result)
        self.assertIn("SIGMA_DEVIATION", result.pattern_type)

    def test_z_score_normal_value(self):
        # Value of 10.3 with history around 10 should NOT be anomalous
        historical = [10.0, 11.0, 9.0, 10.5, 10.2]
        result = self.detector.evaluate_metric(
            MetricType.COMMUNITY_SIZE, 10.3, historical_values=historical
        )
        self.assertIsNone(result)

    def test_z_score_fallback_insufficient_history(self):
        # With < 3 historical values, should fall back to simple threshold
        result = self.detector.evaluate_metric(
            MetricType.COMMUNITY_SIZE, 15.0, historical_values=[10.0, 11.0]
        )
        self.assertIsNotNone(result)
        # Should be simple threshold result, not Z-score
        self.assertEqual(result.pattern_type, "COMMUNITY_SIZE")

    def test_z_score_zero_stddev(self):
        # All identical values => std_dev=0 => should return None
        result = self.detector.evaluate_complex_anomaly(
            MetricType.COMMUNITY_SIZE, 10.0, historical_values=[10.0, 10.0, 10.0]
        )
        self.assertIsNone(result)

    def test_sensitivity_multiplier(self):
        sensitive_profile = ThresholdProfile(
            name="sensitive",
            thresholds={MetricType.COMMUNITY_SIZE: 10.0},
            sensitivity_multiplier=0.5,  # Makes threshold effectively 5.0
        )
        self.detector.register_profile("sensitive_ctx", sensitive_profile)
        # 7.0 > 10.0 * 0.5 = 5.0, so should trigger
        result = self.detector.evaluate_metric(
            MetricType.COMMUNITY_SIZE, 7.0, context_id="sensitive_ctx"
        )
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
