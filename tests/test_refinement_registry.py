import os
import tempfile
import pytest
from domain.core.refinement_registry import RefinementRegistry
from domain.supporting.ledger import StructuralLedger


class _FakeProposal:
    def __init__(self, target_component, proposed_state):
        self.target_component = target_component
        self.proposed_state = proposed_state


class TestRefinementRegistry:
    # Use custom allowed_targets so unit tests exercise registry mechanics
    # without being tied to the production allowlist.
    _TEST_TARGETS = {"prompt_v1", "a", "b"}

    def test_fresh_registry_is_empty(self):
        reg = RefinementRegistry()
        assert reg.get_all() == {}

    def test_apply_stores_refinement(self):
        reg = RefinementRegistry(allowed_targets=self._TEST_TARGETS)
        reg.apply(_FakeProposal("prompt_v1", "new system prompt"))
        assert reg.get_refinement("prompt_v1") == "new system prompt"

    def test_apply_overwrites_existing(self):
        reg = RefinementRegistry(allowed_targets=self._TEST_TARGETS)
        reg.apply(_FakeProposal("prompt_v1", "first"))
        reg.apply(_FakeProposal("prompt_v1", "second"))
        assert reg.get_refinement("prompt_v1") == "second"

    def test_get_refinement_returns_none_for_unknown(self):
        reg = RefinementRegistry()
        assert reg.get_refinement("nonexistent") is None

    def test_get_all_returns_copy(self):
        reg = RefinementRegistry(allowed_targets=self._TEST_TARGETS)
        reg.apply(_FakeProposal("a", "1"))
        snapshot = reg.get_all()
        snapshot["a"] = "mutated"
        assert reg.get_refinement("a") == "1"

    def test_multiple_targets_independent(self):
        reg = RefinementRegistry(allowed_targets=self._TEST_TARGETS)
        reg.apply(_FakeProposal("a", "1"))
        reg.apply(_FakeProposal("b", "2"))
        assert reg.get_refinement("a") == "1"
        assert reg.get_refinement("b") == "2"
        assert len(reg.get_all()) == 2

    def test_apply_rejects_target_not_in_allowlist(self):
        reg = RefinementRegistry()  # uses default ALLOWED_TARGETS
        reg.apply(_FakeProposal("evil_target", "payload"))
        assert reg.get_all() == {}


class TestRefinementRegistryPersistence:
    """Verify refinements survive a fresh RefinementRegistry instance."""
    _TEST_TARGETS = {"prompt_v1", "tool_cfg", "a"}

    @pytest.fixture
    def ledger(self):
        db_path = os.path.join(tempfile.mkdtemp(), "registry_persist.db")
        return StructuralLedger(db_path)

    def test_refinements_persist_across_instances(self, ledger):
        reg1 = RefinementRegistry(ledger, allowed_targets=self._TEST_TARGETS)
        reg1.apply(_FakeProposal("prompt_v1", "be concise"))
        reg1.apply(_FakeProposal("tool_cfg", "enable_search"))

        # Create a brand-new registry backed by the same DB
        reg2 = RefinementRegistry(ledger, allowed_targets=self._TEST_TARGETS)
        assert reg2.get_refinement("prompt_v1") == "be concise"
        assert reg2.get_refinement("tool_cfg") == "enable_search"
        assert len(reg2.get_all()) == 2

    def test_overwrite_persists(self, ledger):
        reg1 = RefinementRegistry(ledger, allowed_targets=self._TEST_TARGETS)
        reg1.apply(_FakeProposal("prompt_v1", "first"))
        reg1.apply(_FakeProposal("prompt_v1", "second"))

        reg2 = RefinementRegistry(ledger, allowed_targets=self._TEST_TARGETS)
        assert reg2.get_refinement("prompt_v1") == "second"

    def test_no_ledger_means_no_persistence(self):
        """Without a ledger, registry is purely in-memory (no crash)."""
        reg = RefinementRegistry(allowed_targets=self._TEST_TARGETS)
        reg.apply(_FakeProposal("a", "1"))
        assert reg.get_refinement("a") == "1"

        # A second instance has no knowledge of the first
        reg2 = RefinementRegistry(allowed_targets=self._TEST_TARGETS)
        assert reg2.get_all() == {}
