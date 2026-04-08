from domain.core.refinement_registry import RefinementRegistry


class _FakeProposal:
    def __init__(self, target_component, proposed_state):
        self.target_component = target_component
        self.proposed_state = proposed_state


class TestRefinementRegistry:
    def test_fresh_registry_is_empty(self):
        reg = RefinementRegistry()
        assert reg.get_all() == {}

    def test_apply_stores_refinement(self):
        reg = RefinementRegistry()
        reg.apply(_FakeProposal("prompt_v1", "new system prompt"))
        assert reg.get_refinement("prompt_v1") == "new system prompt"

    def test_apply_overwrites_existing(self):
        reg = RefinementRegistry()
        reg.apply(_FakeProposal("prompt_v1", "first"))
        reg.apply(_FakeProposal("prompt_v1", "second"))
        assert reg.get_refinement("prompt_v1") == "second"

    def test_get_refinement_returns_none_for_unknown(self):
        reg = RefinementRegistry()
        assert reg.get_refinement("nonexistent") is None

    def test_get_all_returns_copy(self):
        reg = RefinementRegistry()
        reg.apply(_FakeProposal("a", "1"))
        snapshot = reg.get_all()
        snapshot["a"] = "mutated"
        assert reg.get_refinement("a") == "1"

    def test_multiple_targets_independent(self):
        reg = RefinementRegistry()
        reg.apply(_FakeProposal("a", "1"))
        reg.apply(_FakeProposal("b", "2"))
        assert reg.get_refinement("a") == "1"
        assert reg.get_refinement("b") == "2"
        assert len(reg.get_all()) == 2
