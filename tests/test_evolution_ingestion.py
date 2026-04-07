import asyncio
import os
import shutil
import pytest

from domain.core.semantic_memory import SemanticMemory
from domain.core.agents_impl import ResearcherAgent, AuditorAgent
from application.orchestrator import Orchestrator
from domain.core.ports import BaseLLMInterface
from domain.core.semantic_ingestor import SemanticIngestor
from typing import Dict, Any


class MockLLM(BaseLLMInterface):
    def complete(self, prompt: str, system_prompt: str = None) -> str:
        if "Synthesize" in prompt or "intelligence" in prompt.lower():
            return "The structural audit confirmed that the ACL layer integration is complete and stable."
        if "Audit" in prompt:
            return "The structural integrity is verified. No issues found."
        if "research" in prompt.lower() or "investigate" in prompt.lower():
            return "The research indicates a major integration milestone was achieved."
        return "Simulated research findings."


@pytest.fixture
def test_dir(tmp_path):
    d = tmp_path / "evolution_test_db"
    d.mkdir()
    return str(d)


@pytest.mark.asyncio
async def test_evolution_ingestion(test_dir):
    """After orchestration, the ingestor should persist synthesized knowledge that is queryable."""
    semantic_memory = SemanticMemory(persist_directory=test_dir)
    mock_llm = MockLLM()
    ingestor = SemanticIngestor(semantic_memory=semantic_memory, llm=mock_llm)

    registry = {"researcher": ResearcherAgent, "auditor": AuditorAgent}
    orchestrator = Orchestrator(registry, llm_interface=mock_llm, ingestor=ingestor)

    complex_goal = "Audit the system and research the recent ACL integration."
    context = {"semantic_memory": semantic_memory, "context_id": "evolution_test"}

    result = await orchestrator.run_goal(complex_goal, context)
    assert result["orchestration_summary"]["agents_dispatched"] >= 1

    # Verify the synthesized sentence landed in memory
    expected_knowledge = "The structural audit confirmed that the ACL layer integration is complete and stable."
    search_results = semantic_memory.query(expected_knowledge, n_results=1, context_id="evolution_test")

    assert len(search_results) > 0, (
        f"Expected synthesized knowledge in memory but found nothing. "
        f"Events: {[r['text'] for r in semantic_memory.list_events(limit=10)]}"
    )
    assert expected_knowledge in search_results[0]["text"]
