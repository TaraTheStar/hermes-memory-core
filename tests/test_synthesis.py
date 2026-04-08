import os
import pytest
from datetime import datetime, timezone

from domain.core.synthesis import SynthesisEngine
from domain.supporting.ledger import StructuralLedger


@pytest.fixture(scope="module")
def test_paths(tmp_path_factory):
    base = tmp_path_factory.mktemp("synthesis")
    db = str(base / "synthesis.db")
    semantic = str(base / "semantic")
    os.makedirs(semantic, exist_ok=True)
    return db, semantic


@pytest.fixture
def engine(test_paths):
    db, semantic = test_paths
    return SynthesisEngine(semantic, db)


@pytest.fixture
def ledger(test_paths):
    db, _ = test_paths
    return StructuralLedger(db)


def test_temporal_scan_empty(engine):
    """Temporal scan on empty data should return 0 edges."""
    result = engine.run_temporal_correlation_scan()
    assert result == 0


def test_cooccurrence_scan_empty(engine):
    """Cooccurrence scan with no events should return 0."""
    result = engine.run_semantic_cooccurrence_scan()
    assert result == 0


def test_attribute_symmetry_scan_empty(engine):
    """Attribute scan with no skills should return 0."""
    result = engine.run_attribute_symmetry_scan()
    assert result == 0


def test_temporal_scan_skips_bad_timestamps(engine):
    """Events with missing or malformed timestamps should be skipped, not crash."""
    engine.semantic_memory.add_event(
        text="Event with no timestamp",
        metadata={"type": "test"},
    )
    engine.semantic_memory.add_event(
        text="Event with bad timestamp",
        metadata={"type": "test", "timestamp": "not-a-date"},
    )
    result = engine.run_temporal_correlation_scan()
    assert isinstance(result, int)
    assert result == 0, "Bad-timestamp events should not produce edges"


def test_temporal_scan_creates_edges(engine, ledger):
    """Events matching skill names within the time window should create edges."""
    skill_id = ledger.add_skill("Python", "Programming language")
    now = datetime.now(timezone.utc)
    engine.semantic_memory.add_event(
        text="I've been practicing python extensively today",
        metadata={"type": "learning", "timestamp": now.isoformat()},
    )
    result = engine.run_temporal_correlation_scan()
    assert result >= 1, "Expected at least one edge from skill-event correlation"


def test_incremental_scan(engine):
    """Second scan should not reprocess old events."""
    now = datetime.now(timezone.utc)
    engine.semantic_memory.add_event(
        text="First event for incremental test",
        metadata={"type": "test", "timestamp": now.isoformat()},
    )
    engine.run_temporal_correlation_scan()

    # Second scan with no new events
    result = engine.run_temporal_correlation_scan()
    assert result == 0


class TestSynthesisCooccurrence:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        db = str(tmp_path / "synthesis_cooc.db")
        semantic = str(tmp_path / "semantic_cooc")
        os.makedirs(semantic, exist_ok=True)
        self.engine = SynthesisEngine(semantic, db)

    def test_cooccurrence_needs_two_events(self):
        """Cooccurrence scan needs at least 2 events."""
        now = datetime.now(timezone.utc)
        self.engine.semantic_memory.add_event(
            text="Solo event",
            metadata={"type": "test", "timestamp": now.isoformat()},
        )
        result = self.engine.run_semantic_cooccurrence_scan()
        assert result == 0


class TestSynthesisEdgeCases:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        db = str(tmp_path / "synthesis_edge.db")
        semantic = str(tmp_path / "semantic")
        os.makedirs(semantic, exist_ok=True)

        self.engine = SynthesisEngine(semantic, db)
        self.ledger = self.engine.ledger

    def test_skill_with_no_last_used_skipped(self):
        """Skills with last_used=None should be skipped in temporal scan."""
        # Add a skill with no last_used
        with self.ledger.session_scope() as session:
            from domain.core.models import Skill
            skill = Skill(id="sk_nolastused", name="orphan_skill",
                          proficiency_level=0.5, last_used=None)
            session.add(skill)

        now = datetime.now(timezone.utc)
        self.engine.semantic_memory.add_event(
            text="orphan_skill is mentioned here",
            metadata={"type": "test", "timestamp": now.isoformat()},
        )
        result = self.engine.run_temporal_correlation_scan()
        assert result == 0

    def test_watermark_persists_across_instances(self):
        """Watermark saved by _save_watermark should be loadable by _load_watermark."""
        test_time = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        self.engine._save_watermark(SynthesisEngine._TEMPORAL_WATERMARK_KEY, test_time)

        # Load the watermark fresh from DB (bypassing in-memory state)
        loaded = self.engine._load_watermark(SynthesisEngine._TEMPORAL_WATERMARK_KEY)
        assert loaded is not None
        assert loaded == test_time

    def test_cooccurrence_similarity_exception_handled(self):
        """If get_similarity raises, the scan should continue without crashing."""
        now = datetime.now(timezone.utc)
        self.engine.semantic_memory.add_event(
            text="Event alpha for similarity test",
            metadata={"type": "test", "timestamp": now.isoformat()},
        )
        self.engine.semantic_memory.add_event(
            text="Event beta for similarity test",
            metadata={"type": "test", "timestamp": now.isoformat()},
        )

        from unittest.mock import patch
        with patch.object(self.engine.semantic_memory, 'get_similarity',
                          side_effect=RuntimeError("embedding failed")):
            result = self.engine.run_semantic_cooccurrence_scan()
            assert result == 0  # No edges created, but no crash

    def test_load_watermark_with_naive_datetime(self):
        """_load_watermark should handle naive (no tzinfo) datetimes."""
        # Persist a naive ISO string (no timezone suffix)
        naive_iso = "2025-01-01T12:00:00"
        self.ledger.set_identity_marker(
            SynthesisEngine._TEMPORAL_WATERMARK_KEY,
            naive_iso,
            confidence=1.0
        )
        loaded = self.engine._load_watermark(SynthesisEngine._TEMPORAL_WATERMARK_KEY)
        assert loaded is not None
        assert loaded.tzinfo is not None  # Should have been upgraded to UTC

    def test_load_watermark_with_malformed_string(self):
        """_load_watermark should return None for unparseable values."""
        self.ledger.set_identity_marker(
            SynthesisEngine._TEMPORAL_WATERMARK_KEY,
            "not-a-date",
            confidence=1.0
        )
        loaded = self.engine._load_watermark(SynthesisEngine._TEMPORAL_WATERMARK_KEY)
        assert loaded is None


class TestAttributeSymmetryScan:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        db = str(tmp_path / "symmetry.db")
        semantic = str(tmp_path / "semantic")
        os.makedirs(semantic, exist_ok=True)
        self.engine = SynthesisEngine(semantic, db)
        self.ledger = self.engine.ledger

    def test_keyword_intersection_creates_edge(self):
        """Skills sharing a symmetry keyword should produce an edge."""
        self.ledger.add_skill("python scripting", "writing python scripts")
        self.ledger.add_skill("python automation", "automating with python")
        result = self.engine.run_attribute_symmetry_scan()
        assert result >= 1

    def test_substring_containment_creates_edge(self):
        """If one skill name is a substring of another, an edge should be created."""
        self.ledger.add_skill("rust", "systems language")
        self.ledger.add_skill("rust async", "async programming in rust")
        result = self.engine.run_attribute_symmetry_scan()
        assert result >= 1

    def test_unrelated_skills_no_edge(self):
        """Skills with no keyword overlap or substring relation should not produce edges."""
        self.ledger.add_skill("cooking", "making food", proficiency=0.5)
        self.ledger.add_skill("gardening", "growing plants", proficiency=0.5)
        result = self.engine.run_attribute_symmetry_scan()
        assert result == 0

    def test_no_duplicate_edges_on_rescan(self):
        """Running the scan twice should not create duplicate edges."""
        self.ledger.add_skill("python web", "web dev with python")
        self.ledger.add_skill("python data", "data science with python")
        first = self.engine.run_attribute_symmetry_scan()
        second = self.engine.run_attribute_symmetry_scan()
        assert first >= 1
        assert second == 0

    def test_custom_symmetry_keywords(self, tmp_path):
        """Custom symmetry_keywords should be used instead of defaults."""
        db = str(tmp_path / "custom_kw.db")
        semantic = str(tmp_path / "custom_kw_semantic")
        os.makedirs(semantic, exist_ok=True)
        engine = SynthesisEngine(semantic, db, symmetry_keywords={"cooking"})
        engine.ledger.add_skill("cooking basics", "basic cooking skills")
        engine.ledger.add_skill("cooking advanced", "advanced cooking techniques")
        result = engine.run_attribute_symmetry_scan()
        assert result >= 1
