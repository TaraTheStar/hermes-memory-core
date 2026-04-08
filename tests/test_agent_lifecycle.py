"""Tests for HermesAgent lifecycle error paths and agent implementations."""
import pytest
from unittest.mock import MagicMock
from domain.core.agent import HermesAgent, AgentTask, AgentResult, AgentStatus


class _ExplodingPlanAgent(HermesAgent):
    async def _plan(self, task, context):
        raise ValueError("plan failed")

    async def _execute_plan(self, plan, context):
        return []

    async def _reflect(self, findings, task, context):
        return AgentResult("ok", 1.0, [])


class _ExplodingExecuteAgent(HermesAgent):
    async def _plan(self, task, context):
        return [{"action": "go"}]

    async def _execute_plan(self, plan, context):
        raise RuntimeError("execute failed")

    async def _reflect(self, findings, task, context):
        return AgentResult("ok", 1.0, [])


class _ExplodingReflectAgent(HermesAgent):
    async def _plan(self, task, context):
        return [{"action": "go"}]

    async def _execute_plan(self, plan, context):
        return [{"data": "ok"}]

    async def _reflect(self, findings, task, context):
        raise RuntimeError("reflect failed")


@pytest.mark.asyncio
async def test_plan_exception_sets_failed():
    """Exception in _plan should set status to FAILED and return confidence 0."""
    agent = _ExplodingPlanAgent("test_01", "tester", MagicMock())
    result = await agent.run(AgentTask("do something"), {})
    assert agent.status == AgentStatus.FAILED
    assert result.confidence == 0.0
    assert result.status == AgentStatus.FAILED
    assert "plan failed" in result.finding


@pytest.mark.asyncio
async def test_execute_exception_sets_failed():
    """Exception in _execute_plan should set status to FAILED."""
    agent = _ExplodingExecuteAgent("test_02", "tester", MagicMock())
    result = await agent.run(AgentTask("do something"), {})
    assert agent.status == AgentStatus.FAILED
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_reflect_exception_sets_failed():
    """Exception in _reflect should set status to FAILED."""
    agent = _ExplodingReflectAgent("test_03", "tester", MagicMock())
    result = await agent.run(AgentTask("do something"), {})
    assert agent.status == AgentStatus.FAILED
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_error_logged_in_history():
    """Failed agent should have an ERROR entry in history."""
    agent = _ExplodingPlanAgent("test_04", "tester", MagicMock())
    await agent.run(AgentTask("do something"), {})
    error_entries = [h for h in agent.history if h["level"] == "ERROR"]
    assert len(error_entries) >= 1
