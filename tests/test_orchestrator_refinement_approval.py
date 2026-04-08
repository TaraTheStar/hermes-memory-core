"""Tests for Orchestrator._handle_refinement_proposals and _perform_meta_reflection."""
import json
import pytest
from unittest.mock import MagicMock
from application.orchestrator import Orchestrator
from domain.core.agent import HermesAgent, AgentTask, AgentResult, AgentStatus
from domain.core.refinement_registry import RefinementRegistry


class _MockLLM:
    def __init__(self, response):
        self._response = response

    def complete(self, prompt, **kwargs):
        if callable(self._response):
            return self._response(prompt)
        return self._response


class _SimpleAgent(HermesAgent):
    async def _plan(self, task, context):
        return [{"action": "noop"}]

    async def _execute_plan(self, plan, context):
        return []

    async def _reflect(self, findings, task, context):
        return AgentResult("Done", 0.9, [], status=AgentStatus.COMPLETED)


def _make_proposal(**overrides):
    p = MagicMock()
    p.proposal_type = overrides.get("proposal_type", "prompt_update")
    p.target_component = overrides.get("target_component", "researcher_prompt")
    p.current_state = overrides.get("current_state", "old prompt")
    p.proposed_state = overrides.get("proposed_state", "new prompt")
    p.rationale = overrides.get("rationale", "improves accuracy")
    return p


# ---------------------------------------------------------------------------
# _handle_refinement_proposals tests
# ---------------------------------------------------------------------------

class TestHandleRefinementProposals:
    @pytest.mark.asyncio
    async def test_approved_proposal_applies_to_registry(self):
        """When LLM returns approved: true (bool), proposal is applied."""
        llm = _MockLLM(json.dumps({"approved": True, "reasoning": "looks good"}))
        registry = RefinementRegistry()
        orch = Orchestrator(
            {"researcher": _SimpleAgent},
            llm_interface=llm,
            refinement_registry=registry,
        )
        proposal = _make_proposal()
        await orch._handle_refinement_proposals([proposal], {})
        assert registry.get_refinement("researcher_prompt") == "new prompt"

    @pytest.mark.asyncio
    async def test_rejected_proposal_not_applied(self):
        """When LLM returns approved: false, proposal is NOT applied."""
        llm = _MockLLM(json.dumps({"approved": False, "reasoning": "risky"}))
        registry = RefinementRegistry()
        orch = Orchestrator(
            {"researcher": _SimpleAgent},
            llm_interface=llm,
            refinement_registry=registry,
        )
        await orch._handle_refinement_proposals([_make_proposal()], {})
        assert registry.get_all() == {}

    @pytest.mark.asyncio
    async def test_truthy_non_bool_rejected(self):
        """Truthy non-bool values like 'yes', 1, 'true' must NOT be treated as approval."""
        for truthy_value in ["yes", 1, "true", "maybe", [1]]:
            llm = _MockLLM(json.dumps({"approved": truthy_value, "reasoning": "test"}))
            registry = RefinementRegistry()
            orch = Orchestrator(
                {"researcher": _SimpleAgent},
                llm_interface=llm,
                refinement_registry=registry,
            )
            await orch._handle_refinement_proposals([_make_proposal()], {})
            assert registry.get_all() == {}, f"approved={truthy_value!r} should be rejected"

    @pytest.mark.asyncio
    async def test_non_dict_response_skipped(self):
        """If LLM returns a JSON array or string, proposal is skipped."""
        llm = _MockLLM(json.dumps([{"approved": True}]))
        registry = RefinementRegistry()
        orch = Orchestrator(
            {"researcher": _SimpleAgent},
            llm_interface=llm,
            refinement_registry=registry,
        )
        await orch._handle_refinement_proposals([_make_proposal()], {})
        assert registry.get_all() == {}

    @pytest.mark.asyncio
    async def test_malformed_json_skipped(self):
        """Invalid JSON from LLM should not crash and proposal is skipped."""
        llm = _MockLLM("not json at all")
        registry = RefinementRegistry()
        orch = Orchestrator(
            {"researcher": _SimpleAgent},
            llm_interface=llm,
            refinement_registry=registry,
        )
        await orch._handle_refinement_proposals([_make_proposal()], {})
        assert registry.get_all() == {}

    @pytest.mark.asyncio
    async def test_target_not_in_allowlist_rejected(self):
        """Even if LLM approves, a target outside the allowlist is rejected by the registry."""
        llm = _MockLLM(json.dumps({"approved": True, "reasoning": "ok"}))
        registry = RefinementRegistry()  # default allowlist
        orch = Orchestrator(
            {"researcher": _SimpleAgent},
            llm_interface=llm,
            refinement_registry=registry,
        )
        proposal = _make_proposal(target_component="evil_component")
        await orch._handle_refinement_proposals([proposal], {})
        assert registry.get_all() == {}

    @pytest.mark.asyncio
    async def test_markdown_fenced_json_parsed(self):
        """LLM response wrapped in markdown fences should be parsed correctly."""
        raw = '```json\n' + json.dumps({"approved": True, "reasoning": "ok"}) + '\n```'
        llm = _MockLLM(raw)
        registry = RefinementRegistry()
        orch = Orchestrator(
            {"researcher": _SimpleAgent},
            llm_interface=llm,
            refinement_registry=registry,
        )
        await orch._handle_refinement_proposals([_make_proposal()], {})
        assert registry.get_refinement("researcher_prompt") == "new prompt"


# ---------------------------------------------------------------------------
# _perform_meta_reflection tests
# ---------------------------------------------------------------------------

class TestPerformMetaReflection:
    def _low_confidence_report(self, confidence=0.3, dispatched=1):
        return {
            "orchestration_summary": {
                "aggregate_confidence": confidence,
                "agents_dispatched": dispatched,
            },
            "agent_findings": [],
        }

    @pytest.mark.asyncio
    async def test_allowed_role_gets_registered(self):
        """An allowed role name from the LLM should be registered."""
        llm = _MockLLM(json.dumps({"role_name": "analyst", "description": "data analyst"}))
        orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
        await orch._perform_meta_reflection("complex analysis", self._low_confidence_report())
        assert "analyst" in orch.registry

    @pytest.mark.asyncio
    async def test_disallowed_role_rejected(self):
        """A role name NOT in ALLOWED_BOOTSTRAP_ROLES should be rejected."""
        llm = _MockLLM(json.dumps({"role_name": "admin", "description": "admin access"}))
        orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
        await orch._perform_meta_reflection("escalate privileges", self._low_confidence_report())
        assert "admin" not in orch.registry

    @pytest.mark.asyncio
    async def test_existing_role_not_re_registered(self):
        """If the suggested role already exists, it should not be overwritten."""
        llm = _MockLLM(json.dumps({"role_name": "analyst", "description": "new version"}))
        orch = Orchestrator({"researcher": _SimpleAgent, "analyst": _SimpleAgent}, llm_interface=llm)
        original_class = orch.registry["analyst"]
        await orch._perform_meta_reflection("deep analysis", self._low_confidence_report())
        assert orch.registry["analyst"] is original_class

    @pytest.mark.asyncio
    async def test_invalid_chars_rejected(self):
        """Role names with special characters should be rejected."""
        llm = _MockLLM(json.dumps({"role_name": "role;DROP TABLE", "description": "injection"}))
        orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
        await orch._perform_meta_reflection("do something", self._low_confidence_report())
        assert "role;DROP TABLE" not in orch.registry
        assert len(orch.registry) == 1  # only original "researcher"

    @pytest.mark.asyncio
    async def test_null_role_name_no_action(self):
        """When LLM returns role_name: null, no role should be registered."""
        llm = _MockLLM(json.dumps({"role_name": None, "description": "No new role needed."}))
        orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
        await orch._perform_meta_reflection("simple task", self._low_confidence_report())
        assert len(orch.registry) == 1

    @pytest.mark.asyncio
    async def test_high_confidence_skips_reflection(self):
        """When confidence is above threshold, meta-reflection should not trigger."""
        call_count = 0
        def counting_llm(prompt):
            nonlocal call_count
            call_count += 1
            return json.dumps({"role_name": "analyst", "description": "test"})

        llm = _MockLLM(counting_llm)
        orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
        report = self._low_confidence_report(confidence=0.9, dispatched=1)
        await orch._perform_meta_reflection("easy task", report)
        assert call_count == 0
        assert len(orch.registry) == 1

    @pytest.mark.asyncio
    async def test_llm_exception_does_not_crash(self):
        """An LLM exception in meta-reflection should be caught gracefully."""
        llm = MagicMock()
        llm.complete.side_effect = RuntimeError("connection lost")
        orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
        # Should not raise
        await orch._perform_meta_reflection("do something", self._low_confidence_report())
        assert len(orch.registry) == 1
