import asyncio
import os
import shutil
import pytest

from domain.core.semantic_memory import SemanticMemory
from domain.core.agents_impl import ResearcherAgent
from application.orchestrator import Orchestrator
from domain.core.ports import BaseLLMInterface
from domain.core.semantic_ingestor import SemanticIngestor


class MockLLM(BaseLLMInterface):
    def complete(self, prompt: str, system_prompt: str = None) -> str:
        return "The integration of the new module was successful and enhanced system connectivity."


@pytest.fixture
def test_dir(tmp_path):
    d = tmp_path / "ingestion_test_db"
    d.mkdir()
    return str(d)


@pytest.mark.asyncio
async def test_ingestion_loop(test_dir):
    """After orchestration with an ingestor, at least one event should exist in memory."""
    sm = SemanticMemory(persist_directory=test_dir)
    mock_llm = MockLLM()
    ingestor = SemanticIngestor(semantic_memory=sm, llm=mock_llm)

    registry = {"researcher": ResearcherAgent}
    orch = Orchestrator(registry=registry, llm_interface=mock_llm, ingestor=ingestor)

    goal = "Research the importance of module integration."
    context = {"context_id": "test_context"}
    await orch.run_goal(goal, context)

    events = sm.list_events(limit=5)
    assert len(events) > 0, "Expected at least one event in memory after orchestration"
    assert any("integration" in e["text"].lower() for e in events)
