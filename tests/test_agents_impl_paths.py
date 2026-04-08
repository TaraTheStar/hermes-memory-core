"""Tests for ResearcherAgent, AuditorAgent, and RefinementAgent edge case paths."""
import json
import os
import tempfile
import shutil
import pytest
from unittest.mock import MagicMock
from domain.core.agents_impl import ResearcherAgent, AuditorAgent, RefinementAgent
from domain.core.agent import AgentTask, AgentStatus, RefinementProposal
from domain.core.semantic_memory import SemanticMemory
from domain.supporting.ledger import StructuralLedger
from domain.core.models import Skill, RelationalEdge


@pytest.fixture
def semantic_memory():
    tmpdir = tempfile.mkdtemp()
    mem = SemanticMemory(tmpdir)
    yield mem
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def ledger():
    db_path = os.path.join(tempfile.mkdtemp(), "test.db")
    return StructuralLedger(db_path)


@pytest.mark.asyncio
async def test_researcher_no_memory_error_finding():
    """ResearcherAgent without semantic_memory should report an error."""
    agent = ResearcherAgent("r01", "researcher", MagicMock())
    result = await agent.run(AgentTask("find something"), {})
    assert "No semantic memory" in result.finding
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_researcher_has_error_sets_zero_confidence(semantic_memory):
    """ResearcherAgent error finding should set confidence to 0."""
    agent = ResearcherAgent("r02", "researcher", MagicMock())
    # Context without semantic_memory triggers error
    result = await agent.run(AgentTask("find it"), {})
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_auditor_no_ledger_error_finding():
    """AuditorAgent without ledger should report an error."""
    agent = AuditorAgent("a01", "auditor", MagicMock())
    result = await agent.run(AgentTask("check integrity"), {})
    assert "No structural ledger" in result.finding
    assert result.confidence <= 0.1


@pytest.mark.asyncio
async def test_auditor_orphaned_edges_low_confidence(ledger):
    """AuditorAgent should report low confidence when orphaned edges exist."""
    # Create an edge with a target that doesn't exist in any entity table
    ledger.add_skill("existing_skill", "a skill")
    with ledger.session_scope() as session:
        edge = RelationalEdge(
            id="edge_orphan",
            source_id="sk_nonexistent",
            target_id="sk_also_nonexistent",
            relationship_type="test_link",
            weight=1.0
        )
        session.add(edge)

    agent = AuditorAgent("a02", "auditor", MagicMock())
    result = await agent.run(AgentTask("check integrity"), {"structural_ledger": ledger})
    assert result.confidence <= 0.4
    assert "orphaned" in result.finding.lower()


@pytest.mark.asyncio
async def test_auditor_cross_domain_edge_not_orphaned(ledger):
    """Cross-domain edges (temporal_context) should only require source to exist."""
    sid = ledger.add_skill("MySkill", "a skill")
    with ledger.session_scope() as session:
        edge = RelationalEdge(
            id="edge_cross",
            source_id=sid,
            target_id="evt_chromadb_id",  # This is a ChromaDB ID, not in structural DB
            relationship_type="temporal_context",
            weight=0.5
        )
        session.add(edge)

    agent = AuditorAgent("a03", "auditor", MagicMock())
    result = await agent.run(AgentTask("audit"), {"structural_ledger": ledger})
    # The cross-domain edge should NOT be counted as orphaned since source exists
    assert "no orphaned" in result.finding.lower() or result.confidence >= 0.8
    assert result.confidence >= 0.8


@pytest.mark.asyncio
async def test_auditor_empty_ledger_low_confidence(ledger):
    """AuditorAgent on empty ledger should warn about no entities."""
    agent = AuditorAgent("a04", "auditor", MagicMock())
    result = await agent.run(AgentTask("audit"), {"structural_ledger": ledger})
    assert result.confidence <= 0.2
    assert "no entities" in result.finding.lower()


# ── RefinementAgent tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refinement_agent_no_proposal_in_context():
    """RefinementAgent without a proposal in context should report an error."""
    agent = RefinementAgent("ref01", "refinement", MagicMock())
    result = await agent.run(AgentTask("evaluate proposal"), {})
    assert "No active refinement proposal" in result.finding
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_refinement_agent_approved_proposal():
    """RefinementAgent should report high confidence when LLM approves."""
    mock_llm = MagicMock()
    mock_llm.complete.return_value = json.dumps({
        "approved": True,
        "reasoning": "The change is safe and well-scoped."
    })
    proposal = RefinementProposal(
        proposal_type="PROMPT_REFINEMENT",
        target_component="researcher_prompt",
        current_state="generic prompt",
        proposed_state="specialized prompt",
        rationale="improve accuracy"
    )
    agent = RefinementAgent("ref02", "refinement", mock_llm)
    result = await agent.run(AgentTask("evaluate"), {"active_refinement_proposal": proposal})
    assert "APPROVED" in result.finding
    assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_refinement_agent_rejected_proposal():
    """RefinementAgent should report moderate confidence when LLM rejects."""
    mock_llm = MagicMock()
    mock_llm.complete.return_value = json.dumps({
        "approved": False,
        "reasoning": "The change is too risky."
    })
    proposal = RefinementProposal(
        proposal_type="TOOL_EXPANSION",
        target_component="auditor_tools",
        current_state="current tools",
        proposed_state="expanded tools",
        rationale="need more audit capabilities"
    )
    agent = RefinementAgent("ref03", "refinement", mock_llm)
    result = await agent.run(AgentTask("evaluate"), {"active_refinement_proposal": proposal})
    assert "REJECTED" in result.finding
    assert result.confidence == 0.5


@pytest.mark.asyncio
async def test_refinement_agent_llm_failure():
    """RefinementAgent should handle LLM failures gracefully."""
    mock_llm = MagicMock()
    mock_llm.complete.side_effect = RuntimeError("LLM connection failed")
    proposal = RefinementProposal(
        proposal_type="PROMPT_REFINEMENT",
        target_component="test",
        current_state="a",
        proposed_state="b",
        rationale="reason"
    )
    agent = RefinementAgent("ref04", "refinement", mock_llm)
    result = await agent.run(AgentTask("evaluate"), {"active_refinement_proposal": proposal})
    assert "Critique failed" in result.finding
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_refinement_agent_llm_returns_markdown_fenced_json():
    """RefinementAgent should strip markdown fences from LLM response."""
    mock_llm = MagicMock()
    mock_llm.complete.return_value = '```json\n{"approved": true, "reasoning": "looks good"}\n```'
    proposal = RefinementProposal(
        proposal_type="PROMPT_REFINEMENT",
        target_component="test",
        current_state="a",
        proposed_state="b",
        rationale="reason"
    )
    agent = RefinementAgent("ref05", "refinement", mock_llm)
    result = await agent.run(AgentTask("evaluate"), {"active_refinement_proposal": proposal})
    assert "APPROVED" in result.finding
    assert result.confidence == 0.95
