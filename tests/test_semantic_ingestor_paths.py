"""Tests for SemanticIngestor error and early-return paths."""
import os
import tempfile
import shutil
import pytest
from unittest.mock import MagicMock
from domain.core.semantic_ingestor import SemanticIngestor
from domain.core.semantic_memory import SemanticMemory


@pytest.fixture
def semantic_memory():
    tmpdir = tempfile.mkdtemp()
    mem = SemanticMemory(tmpdir)
    yield mem
    shutil.rmtree(tmpdir, ignore_errors=True)


class _MockLLM:
    def __init__(self, response="A synthesized event about the findings."):
        self._response = response

    def complete(self, prompt, *args, **kwargs):
        return self._response


class _FailingLLM:
    def complete(self, prompt, *args, **kwargs):
        raise RuntimeError("LLM connection failed")


@pytest.mark.asyncio
async def test_ingest_no_findings_returns_false(semantic_memory):
    """When there are no findings, ingest should return False."""
    ingestor = SemanticIngestor(semantic_memory, _MockLLM())
    result = await ingestor.ingest(
        {"goal": "test", "agent_findings": [], "orchestration_summary": {}},
        {}
    )
    assert result is False


@pytest.mark.asyncio
async def test_ingest_short_llm_output_returns_false(semantic_memory):
    """When LLM returns very short text, ingest should return False."""
    ingestor = SemanticIngestor(semantic_memory, _MockLLM(response="Hi"))
    result = await ingestor.ingest(
        {"goal": "test", "agent_findings": [{"finding": "x", "confidence": 0.5}],
         "orchestration_summary": {}},
        {}
    )
    assert result is False


@pytest.mark.asyncio
async def test_ingest_llm_exception_returns_false(semantic_memory):
    """When LLM raises, ingest should catch and return False."""
    ingestor = SemanticIngestor(semantic_memory, _FailingLLM())
    result = await ingestor.ingest(
        {"goal": "test", "agent_findings": [{"finding": "x", "confidence": 0.5}],
         "orchestration_summary": {}},
        {}
    )
    assert result is False


@pytest.mark.asyncio
async def test_ingest_context_id_override(semantic_memory):
    """context_id from context dict should override the default."""
    ingestor = SemanticIngestor(semantic_memory, _MockLLM(), context_id="default_ctx")
    result = await ingestor.ingest(
        {"goal": "test", "agent_findings": [{"finding": "found it", "confidence": 0.9}],
         "orchestration_summary": {"aggregate_confidence": 0.9}},
        {"context_id": "custom_ctx"}
    )
    assert result is True
    # Verify the event was stored with the custom context_id
    events = semantic_memory.list_events(limit=10, context_id="custom_ctx")
    assert len(events) >= 1


@pytest.mark.asyncio
async def test_ingest_metadata_fields(semantic_memory):
    """Ingested events should have correct metadata fields."""
    ingestor = SemanticIngestor(semantic_memory, _MockLLM())
    await ingestor.ingest(
        {"goal": "investigate hub",
         "agent_findings": [
             {"finding": "hub found", "confidence": 0.8},
             {"finding": "confirmed", "confidence": 0.9}
         ],
         "orchestration_summary": {"aggregate_confidence": 0.85}},
        {}
    )
    events = semantic_memory.list_events(limit=1)
    assert len(events) >= 1
    meta = events[0]["metadata"]
    assert meta["type"] == "autonomous_learning"
    assert meta["original_goal"] == "investigate hub"
    assert meta["confidence"] == 0.85
    assert meta["agents_involved"] == 2
