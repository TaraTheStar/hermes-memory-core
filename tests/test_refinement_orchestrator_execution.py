"""Tests for RefinementOrchestrator._execute_proposal and process_refinements."""
import os
import asyncio
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from application.refinement_orchestrator import RefinementOrchestrator
from domain.core.refinement_engine import GraphRefinementProposal
from domain.core.models import RelationalEdge
from domain.core.agents_impl import ResearcherAgent, AuditorAgent


@pytest.fixture
def orch():
    db_path = os.path.join(tempfile.mkdtemp(), "test_refine.db")
    registry = {"researcher": ResearcherAgent, "auditor": AuditorAgent}
    return RefinementOrchestrator(db_path, registry, llm_interface=None)


@pytest.mark.asyncio
async def test_execute_proposal_prune_edge(orch):
    """PRUNE_EDGE with valid target_id should delete the edge and return True."""
    # Create an edge to prune
    with orch.ledger.session_scope() as session:
        from domain.core.models import Skill
        s1 = Skill(id="sk_a", name="a", proficiency_level=0.5)
        s2 = Skill(id="sk_b", name="b", proficiency_level=0.5)
        session.add_all([s1, s2])
        session.flush()
        edge = RelationalEdge(id="e1", source_id="sk_a", target_id="sk_b",
                              relationship_type="test", weight=0.1)
        session.add(edge)

    proposal = GraphRefinementProposal("PRUNE_EDGE", "sk_a->sk_b", "test", {})
    result = await orch._execute_proposal(proposal)
    assert result is True

    # Verify edge is gone
    with orch.ledger.session_scope() as session:
        count = session.query(RelationalEdge).filter_by(source_id="sk_a", target_id="sk_b").count()
        assert count == 0


@pytest.mark.asyncio
async def test_execute_proposal_malformed_target_returns_false(orch):
    """PRUNE_EDGE with no '->' in target_id should return False."""
    proposal = GraphRefinementProposal("PRUNE_EDGE", "bad_target_id", "test", {})
    result = await orch._execute_proposal(proposal)
    assert result is False


@pytest.mark.asyncio
async def test_execute_proposal_unknown_type_returns_false(orch):
    """Unknown proposal type should return False."""
    proposal = GraphRefinementProposal("UNKNOWN_TYPE", "x", "test", {})
    result = await orch._execute_proposal(proposal)
    assert result is False


@pytest.mark.asyncio
async def test_execute_proposal_merge_community_returns_true(orch):
    """MERGE_COMMUNITY (simulated) should return True."""
    proposal = GraphRefinementProposal("MERGE_COMMUNITY", "community_0", "test", {})
    result = await orch._execute_proposal(proposal)
    assert result is True


@pytest.mark.asyncio
async def test_execute_proposal_global_rebalance_returns_true(orch):
    """GLOBAL_REBALANCE (simulated) should return True."""
    proposal = GraphRefinementProposal("GLOBAL_REBALANCE", "graph_root", "test", {})
    result = await orch._execute_proposal(proposal)
    assert result is True


@pytest.mark.asyncio
async def test_process_refinements_no_proposals(orch):
    """When no proposals are found, process_refinements returns 0."""
    count = await orch.process_refinements()
    assert count == 0


@pytest.mark.asyncio
async def test_process_refinements_rejected_proposal_not_counted(orch):
    """Rejected proposals should not increment executed_count."""
    proposal = GraphRefinementProposal("PRUNE_EDGE", "a->b", "low weight", {})

    with patch.object(orch.engine, 'analyze_for_refinement', return_value=[proposal]):
        # Make run_goal return low confidence so _is_approved returns False
        with patch.object(orch.orchestrator, 'run_goal', new_callable=AsyncMock,
                          return_value={"orchestration_summary": {"aggregate_confidence": 0.1}, "agent_findings": []}):
            count = await orch.process_refinements()
            assert count == 0
