"""Tests for SnapshotAnomalyDetector edge cases: nan, degenerate data, hub emergence."""
import os
import uuid
import tempfile
import datetime
from datetime import timezone
import pytest
from domain.supporting.monitor import SnapshotAnomalyDetector, StateTracker
from domain.supporting.monitor_models import GraphSnapshot
from domain.supporting.ledger import StructuralLedger


@pytest.fixture
def ledger():
    db_path = os.path.join(tempfile.mkdtemp(), "monitor_test.db")
    return StructuralLedger(db_path)


def _make_snapshot(ts, density, community_count, centrality_metrics, session):
    snap = GraphSnapshot(
        id=str(uuid.uuid4()),
        timestamp=ts,
        density=density,
        community_count=community_count,
        centrality_metrics=centrality_metrics,
        metadata_tags={}
    )
    session.add(snap)
    return snap


def test_identical_timestamps_does_not_crash(ledger):
    """polyfit with identical timestamps should not crash or produce nan anomalies."""
    detector = SnapshotAnomalyDetector(ledger, sensitivity=2.0)
    base_time = datetime.datetime(2025, 1, 1, tzinfo=timezone.utc)

    with ledger.session_scope() as session:
        # Create 4 historical snapshots all at the same timestamp
        for _ in range(4):
            _make_snapshot(
                base_time, 0.1, 2,
                {"node_a": {"degree": 0.5, "betweenness": 0.1, "eigenvector": 0.1}},
                session
            )

    current = GraphSnapshot(
        id=str(uuid.uuid4()),
        timestamp=base_time,  # Same as all history
        density=0.1,
        community_count=2,
        centrality_metrics={"node_a": {"degree": 0.5, "betweenness": 0.1, "eigenvector": 0.1}},
        metadata_tags={}
    )

    # Should not crash or produce nan-based anomalies
    anomalies = detector.detect_anomalies(current)
    assert isinstance(anomalies, list)


def test_hub_emergence_detection(ledger):
    """A node with rapidly increasing degree should trigger STRUCTURAL_ACCELERATION."""
    detector = SnapshotAnomalyDetector(ledger, sensitivity=0.001)  # Very sensitive
    base_time = datetime.datetime(2025, 1, 1, tzinfo=timezone.utc)

    with ledger.session_scope() as session:
        # Create history with a node whose degree is steadily increasing.
        # Use 1-second intervals so the slope (per second) is large.
        for i in range(5):
            ts = base_time + datetime.timedelta(seconds=i)
            _make_snapshot(
                ts, 0.1, 2,
                {"hub_node": {"degree": float(i + 1), "betweenness": 0.1, "eigenvector": 0.1}},
                session
            )

    current = GraphSnapshot(
        id=str(uuid.uuid4()),
        timestamp=base_time + datetime.timedelta(seconds=6),
        density=0.1,
        community_count=2,
        centrality_metrics={"hub_node": {"degree": 10.0, "betweenness": 0.1, "eigenvector": 0.1}},
        metadata_tags={}
    )

    anomalies = detector.detect_anomalies(current)
    accel_anomalies = [a for a in anomalies if a.anomaly_type == "STRUCTURAL_ACCELERATION"]
    assert len(accel_anomalies) >= 1
    assert "hub_node" in accel_anomalies[0].trigger_data.get("node_id", "")


def test_predict_trend_insufficient_history(ledger):
    """_predict_trend with < 2 items should return zeros."""
    detector = SnapshotAnomalyDetector(ledger)
    result = detector._predict_trend([], "density", datetime.datetime.now(timezone.utc))
    assert result["expected"] == 0.0
    assert result["velocity"] == 0.0


def test_density_divergence_detected(ledger):
    """A sudden density change should be detected as TREND_DIVERGENCE."""
    detector = SnapshotAnomalyDetector(ledger, sensitivity=1.0)
    base_time = datetime.datetime(2025, 1, 1, tzinfo=timezone.utc)

    with ledger.session_scope() as session:
        # Stable history at density ~0.1
        for i in range(5):
            ts = base_time + datetime.timedelta(hours=i)
            _make_snapshot(ts, 0.1, 2, {}, session)

    # Current snapshot with a huge density jump
    current = GraphSnapshot(
        id=str(uuid.uuid4()),
        timestamp=base_time + datetime.timedelta(hours=6),
        density=0.9,
        community_count=2,
        centrality_metrics={},
        metadata_tags={}
    )

    anomalies = detector.detect_anomalies(current)
    trend_anomalies = [a for a in anomalies if a.anomaly_type == "TREND_DIVERGENCE"]
    assert len(trend_anomalies) >= 1
