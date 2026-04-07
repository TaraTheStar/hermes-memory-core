import os
import sys
import shutil
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from domain.core.synthesis import SynthesisEngine
from domain.supporting.ledger import StructuralLedger


class TestSynthesisEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "/tmp/hermes_test_synthesis.db"
        cls.test_semantic_dir = "/tmp/hermes_test_synthesis_semantic"

        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        if os.path.exists(cls.test_semantic_dir):
            shutil.rmtree(cls.test_semantic_dir)
        os.makedirs(cls.test_semantic_dir)

    def setUp(self):
        self.engine = SynthesisEngine(self.test_semantic_dir, self.test_db)
        self.ledger = StructuralLedger(self.test_db)

    def test_temporal_scan_empty(self):
        """Temporal scan on empty data should return 0 edges."""
        result = self.engine.run_temporal_correlation_scan()
        self.assertEqual(result, 0)

    def test_cooccurrence_scan_empty(self):
        """Cooccurrence scan with no events should return 0."""
        result = self.engine.run_semantic_cooccurrence_scan()
        self.assertEqual(result, 0)

    def test_attribute_symmetry_scan_empty(self):
        """Attribute scan with no skills should return 0."""
        result = self.engine.run_attribute_symmetry_scan()
        self.assertEqual(result, 0)

    def test_temporal_scan_skips_bad_timestamps(self):
        """Events with missing or malformed timestamps should be skipped, not crash."""
        # Add an event with no timestamp
        self.engine.semantic_memory.add_event(
            text="Event with no timestamp",
            metadata={"type": "test"}
        )
        # Add an event with a bad timestamp
        self.engine.semantic_memory.add_event(
            text="Event with bad timestamp",
            metadata={"type": "test", "timestamp": "not-a-date"}
        )
        # Should not raise
        result = self.engine.run_temporal_correlation_scan()
        self.assertIsInstance(result, int)

    def test_temporal_scan_creates_edges(self):
        """Events matching skill names within the time window should create edges."""
        skill_id = self.ledger.add_skill("Python", "Programming language")
        now = datetime.now(timezone.utc)
        self.engine.semantic_memory.add_event(
            text="I've been practicing python extensively today",
            metadata={"type": "learning", "timestamp": now.isoformat()}
        )
        result = self.engine.run_temporal_correlation_scan()
        self.assertGreaterEqual(result, 1, "Expected at least one edge from skill-event correlation")

    def test_incremental_scan(self):
        """Second scan should not reprocess old events."""
        now = datetime.now(timezone.utc)
        self.engine.semantic_memory.add_event(
            text="First event for incremental test",
            metadata={"type": "test", "timestamp": now.isoformat()}
        )
        self.engine.run_temporal_correlation_scan()

        # Second scan with no new events
        result = self.engine.run_temporal_correlation_scan()
        self.assertEqual(result, 0)


class TestSynthesisCooccurrence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "/tmp/hermes_test_synthesis_cooc.db"
        cls.test_semantic_dir = "/tmp/hermes_test_synthesis_cooc_semantic"

        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        if os.path.exists(cls.test_semantic_dir):
            shutil.rmtree(cls.test_semantic_dir)
        os.makedirs(cls.test_semantic_dir)

    def test_cooccurrence_needs_two_events(self):
        """Cooccurrence scan needs at least 2 events."""
        engine = SynthesisEngine(self.test_semantic_dir, self.test_db)
        now = datetime.now(timezone.utc)
        engine.semantic_memory.add_event(
            text="Solo event",
            metadata={"type": "test", "timestamp": now.isoformat()}
        )
        result = engine.run_semantic_cooccurrence_scan()
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
