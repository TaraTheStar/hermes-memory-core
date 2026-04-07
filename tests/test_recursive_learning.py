import asyncio
import os
import shutil
import pytest

from domain.core.agent import HermesAgent, AgentStatus, AgentTask, AgentResult
from domain.core.semantic_memory import SemanticMemory
from domain.core.semantic_ingestor import SemanticIngestor
from domain.core.ports import BaseLLMInterface
from application.orchestrator import Orchestrator
from typing import Dict, Any, List


class MockLLM(BaseLLMInterface):
    def complete(self, prompt: str, system_prompt: str = None) -> str:
        if "SYNTHESIZED EVENT:" in prompt:
            return "The integration of the ACL layer was successfully completed and verified across all modules."
        return "Simulated research findings."


class MockResearcher(HermesAgent):
    async def _plan(self, task, context):
        return [{"role": "researcher", "goal": task.goal, "constraints": []}]

    async def _execute_plan(self, plan, context):
        return [{"finding": "ACL layer is fully integrated.", "confidence": 0.9, "evidence": [], "status": AgentStatus.COMPLETED}]

    async def _reflect(self, findings, task, context):
        return AgentResult(findings[0]["finding"], findings[0]["confidence"], findings[0]["evidence"])


class MockAuditor(HermesAgent):
    async def _plan(self, task, context):
        return [{"role": "auditor", "goal": task.goal, "constraints": []}]

    async def _execute_plan(self, plan, context):
        return [{"finding": "Integration verified with 100% success.", "confidence": 0.95, "evidence": [], "status": AgentStatus.COMPLETED}]

    async def _reflect(self, findings, task, context):
        return AgentResult(findings[0]["finding"], findings[0]["confidence"], findings[0]["evidence"])


@pytest.fixture
def test_dir(tmp_path):
    d = tmp_path / "evolution_test_db"
    d.mkdir()
    return str(d)


@pytest.mark.asyncio
async def test_recursive_learning_loop(test_dir):
    """After orchestration with an ingestor, synthesized knowledge should be queryable."""
    sm = SemanticMemory(persist_directory=test_dir)
    mock_llm = MockLLM()
    ingestor = SemanticIngestor(semantic_memory=sm, llm=mock_llm)

    registry = {"researcher": MockResearcher, "auditor": MockAuditor}
    orch = Orchestrator(registry=registry, llm_interface=mock_llm, ingestor=ingestor)

    goal = "Investigate the recent integration of the ACL layer."
    result = await orch.run_goal(goal, context={"context_id": "evolution_test"})

    assert result["orchestration_summary"]["agents_dispatched"] >= 1

    # Verify synthesized knowledge landed in semantic memory
    search_results = sm.query("ACL layer integration", n_results=1, context_id="evolution_test")

    assert len(search_results) > 0, (
        f"Expected synthesized knowledge in memory, but found nothing. "
        f"All events: {sm.list_events(limit=10)}"
    )
