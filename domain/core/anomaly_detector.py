from typing import Dict, Any, Optional, List
import math
from domain.core.anomaly_config import MetricType, ThresholdProfile, ContextualAnomalyConfig
from domain.core.events import DomainEvent, InfrastructureErrorEvent, EventSeverity, PatternDetectedEvent

class AnomalyDetectionError(Exception):
    """Base exception for anomaly detection failures."""
    pass

class ContextualAnomalyDetector:
    """
    The intelligence layer responsible for determining if a change in 
    system metrics constitutes a meaningful anomaly within a given Bounded Context.
    """
    def __init__(self):
        # Registry of profiles: { context_id: ThresholdProfile }
        self._profiles: Dict[str, ThresholdProfile] = {}
        self.GLOBAL_CONTEXT = "global"

    def register_profile(self, context_id: str, profile: ThresholdProfile) -> None:
        """Registers a new threshold profile for a specific context."""
        self._profiles[context_id] = profile

    def _get_profile(self, context_id: str) -> ThresholdProfile:
        """Retrieves the profile for the context, falling back to global."""
        if context_id in self._profiles:
            return self._profiles[context_id]
        return self._profiles.get(self.GLOBAL_CONTEXT, ThresholdProfile(name="default_global"))

    def evaluate_metric(self, metric_type: MetricType, current_value: float, context_id: str = "global") -> Optional[DomainEvent]:
        """
        Evaluates a metric against the profile of the provided context.
        Returns a PatternDetectedEvent if an anomaly is detected, otherwise None.
        """
        profile = self._get_profile(context_id)
        threshold = profile.thresholds.get(metric_type)

        if threshold is None:
            return None

        # Logic: For simplicity in this implementation, we treat thresholds as absolute upper limits.
        # In a production version, this would involve Z-score (sigma) calculations 
        # against a running mean/std-dev stored in the StateRegistry.
        
        is_anomaly = False
        if current_value > threshold * profile.sensitivity_multiplier:
            is_anomaly = True

        if is_anomaly:
            return PatternDetectedEvent(
                severity=EventSeverity.WARNING,
                source="ContextualAnomalyDetector",
                pattern_type=metric_type.name,
                metadata={
                    "context_id": context_id,
                    "value": current_value,
                    "threshold": threshold,
                    "sensitivity": profile.sensitivity_multiplier
                }
            )

        return None

    def evaluate_complex_anomaly(self, metric_type: MetricType, current_value: float, context_id: str = "global", historical_values: List[float] = None) -> Optional[DomainEvent]:
        """
        Advanced evaluation using statistical deviation (Sigma/Z-Score).
        """
        if not historical_values or len(historical_values) < 3:
            # Fall fallback to simple threshold if not enough history
            return self.evaluate_metric(metric_type, current_value, context_id)

        profile = self._get_profile(context_id)
        
        # Calculate mean and standard deviation
        n = len(historical_values)
        mean = sum(historical_values) / n
        variance = sum((x - mean) ** 2 for x in historical_values) / n
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return None

        # Calculate Z-Score
        z_score = abs(current_value - mean) / std_dev

        # Check against profile sensitivity
        # We assume the profile's threshold for this metric is actually a Z-Score target (e.g. 3.0 for 3-sigma)
        threshold = profile.thresholds.get(metric_type, 3.0) 
        
        if z_score > (threshold * profile.sensitivity_multiplier):
            return PatternDetectedEvent(
                severity=EventSeverity.ERROR,
                source="ContextualAnomalyDetector",
                pattern_type=f"{metric_type.name}_SIGMA_DEVIATION",
                metadata={
                    "context_id": context_id,
                    "z_score": z_score,
                    "mean": mean,
                    "std_dev": std_dev,
                    "value": current_value
                }
            )

        return None
