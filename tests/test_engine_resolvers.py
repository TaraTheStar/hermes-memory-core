"""Tests for MemoryEngine entity resolvers and EventExtractor edge cases."""
import os
import tempfile
import shutil
import pytest
from application.engine import MemoryEngine, EventExtractor
from domain.core.models import Event


@pytest.fixture
def engine():
    tmpdir = tempfile.mkdtemp()
    sem_dir = os.path.join(tmpdir, "semantic")
    db_path = os.path.join(tmpdir, "test.db")
    eng = MemoryEngine(semantic_dir=sem_dir, structural_db_path=db_path)
    yield eng
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestEventExtractor:
    def test_love_trigger_importance_3(self):
        """The 'love' trigger should set importance to 3.0."""
        extractor = EventExtractor()
        events = extractor.extract_events("I love Python programming")
        assert len(events) >= 1
        love_events = [e for e in events if "love" in e.metadata.get("trigger", "")]
        assert love_events
        assert love_events[0].metadata["importance"] == 3.0

    def test_fascinated_trigger_importance_3(self):
        """The 'fascinated by' trigger should set importance to 3.0."""
        extractor = EventExtractor()
        events = extractor.extract_events("I am fascinated by quantum computing")
        assert len(events) >= 1
        fasc_events = [e for e in events if "fascinated" in e.metadata.get("trigger", "")]
        assert fasc_events
        assert fasc_events[0].metadata["importance"] == 3.0

    def test_subject_truncation_at_100_chars(self):
        """Subjects longer than 100 characters should be truncated by the regex."""
        extractor = EventExtractor()
        long_subject = "x" * 150
        events = extractor.extract_events(f"I prefer {long_subject}")
        assert len(events) >= 1
        subject = events[0].metadata.get("subject", "")
        assert len(subject) <= 100

    def test_multiple_patterns_in_one_string(self):
        """Multiple patterns should all be extracted."""
        extractor = EventExtractor()
        text = "I love cats. I mastered cooking. My name is Alice."
        events = extractor.extract_events(text)
        types = {e.event_type for e in events}
        assert "preference" in types
        assert "skill" in types
        assert "identity_marker" in types


class TestResolvers:
    def test_resolve_project_with_skills(self, engine):
        """_resolve_project should include connected skills."""
        pid = engine.ledger.add_project("TestProj")
        sid = engine.ledger.add_skill("Python", "Programming language")
        engine.ledger.add_edge(pid, sid, "uses_skill")

        with engine.ledger.session_scope() as session:
            ctx = engine._resolve_project(session, pid)
        assert ctx["type"] == "project"
        assert ctx["name"] == "TestProj"
        assert "skills" in ctx
        assert any(s["name"] == "Python" for s in ctx["skills"])

    def test_resolve_skill_with_projects(self, engine):
        """_resolve_skill should include used_in_projects."""
        pid = engine.ledger.add_project("MyProject")
        sid = engine.ledger.add_skill("Rust", "Systems language")
        engine.ledger.add_edge(pid, sid, "uses_skill")

        with engine.ledger.session_scope() as session:
            ctx = engine._resolve_skill(session, sid)
        assert ctx["type"] == "skill"
        assert ctx["name"] == "Rust"
        assert "used_in_projects" in ctx
        assert any(p["name"] == "MyProject" for p in ctx["used_in_projects"])

    def test_resolve_identity_marker(self, engine):
        """_resolve_identity_marker should return marker fields."""
        mid = engine.ledger.set_identity_marker("name", "Alice", confidence=0.95)

        with engine.ledger.session_scope() as session:
            ctx = engine._resolve_identity_marker(session, mid)
        assert ctx["type"] == "identity_marker"
        assert ctx["key"] == "name"
        assert ctx["value"] == "Alice"
        assert ctx["confidence_score"] == 0.95

    def test_resolve_entity_unknown_prefix(self, engine):
        """Unknown prefix should return empty dict."""
        with engine.ledger.session_scope() as session:
            ctx = engine._resolve_entity(session, "unknown_prefix_123")
        assert ctx == {}

    def test_resolve_entity_exception_returns_error(self, engine):
        """If resolver raises, _resolve_entity exception is caught by query()."""
        # Add an event with a structural_id that will cause a lookup
        engine.semantic_memory.add_event(
            "test event",
            {"type": "test", "structural_id": "proj_nonexistent"}
        )
        # query should not crash, and should include an error or empty context
        results = engine.query("test event", n_results=5)
        # Shouldn't raise; the structural_id just won't find a project
        assert isinstance(results, list)

    def test_resolve_nonexistent_project_returns_empty(self, engine):
        """Resolving a project ID that doesn't exist should return {}."""
        with engine.ledger.session_scope() as session:
            ctx = engine._resolve_project(session, "proj_doesnotexist")
        assert ctx == {}

    def test_resolve_nonexistent_skill_returns_empty(self, engine):
        """Resolving a skill ID that doesn't exist should return {}."""
        with engine.ledger.session_scope() as session:
            ctx = engine._resolve_skill(session, "sk_doesnotexist")
        assert ctx == {}
