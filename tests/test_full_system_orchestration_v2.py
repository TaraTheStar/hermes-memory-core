import asyncio
import os
import shutil
import pytest

from domain.core.semantic_memory import SemanticMemory
from domain.core.agents_impl import ResearcherAgent, AuditorAgent
from domain.supporting.ledger import StructuralLedger
from application.orchestrator import Orchestrator
from domain.core.ports import BaseLLMInterface
from typing import Dict, Any


class MockLLM(BaseLLMInterface):
    def complete(self, prompt: str, system_prompt: str = None) -> str:
        if "Audit" in prompt:
            return "The structural integrity is verified. No issues found."
        if "research" in prompt.lower() or "investigate" in prompt.lower():
            return "The research indicates a major integration milestone was achieved."
        return "Simulated research findings."


@pytest.fixture
def test_dir(tmp_path):
    d = tmp_path / "autonomy_test_db"
    d.mkdir()
    return str(d)


@pytest.mark.asyncio
async def test_full_system_orchestration(test_dir):
    """Orchestrator should dispatch both researcher and auditor agents and aggregate results."""
    semantic_dir = os.path.join(test_dir, "semantic")
    os.makedirs(semantic_dir)
    db_path = os.path.join(test_dir, "test.db")

    semantic_memory = SemanticMemory(persist_directory=semantic_dir)
    ledger = StructuralLedger(db_path)

    # Seed some structural data so the auditor has something to validate
    ledger.add_skill("ACL", "Anti-corruption layer")

    semantic_memory.add_event(
        "The user successfully integrated the ACL layer into the configuration loader.",
        {"type": "milestone"},
        context_id="development"
    )

    registry = {"researcher": ResearcherAgent, "auditor": AuditorAgent}
    mock_llm = MockLLM()
    orchestrator = Orchestrator(registry, mock_llm)

    complex_goal = "Audit the development context and research the recent integration milestones."
    context = {
        "semantic_memory": semantic_memory,
        "structural_ledger": ledger,
        "context_id": "development",
    }

    result = await orchestrator.run_goal(complex_goal, context)

    assert result["orchestration_summary"]["agents_dispatched"] == 2
    assert result["orchestration_summary"]["agents_successful"] >= 1
    assert result["orchestration_summary"]["aggregate_confidence"] > 0

    # Verify findings contain meaningful content
    findings = result["agent_findings"]
    assert len(findings) == 2
    assert any(f["confidence"] > 0 for f in findings)
