"""Tests for Orchestrator._llm_decompose and _execute_agent failure path."""
import asyncio
import json
import pytest
from unittest.mock import MagicMock, AsyncMock
from application.orchestrator import Orchestrator
from domain.core.agent import HermesAgent, AgentTask, AgentResult, AgentStatus


class _MockLLM:
    def __init__(self, response):
        self._response = response

    def complete(self, prompt, **kwargs):
        return self._response


class _FailingAgent(HermesAgent):
    async def _plan(self, task, context):
        raise RuntimeError("agent exploded")

    async def _execute_plan(self, plan, context):
        return []

    async def _reflect(self, findings, task, context):
        return AgentResult("ok", 1.0, [])


class _SimpleAgent(HermesAgent):
    async def _plan(self, task, context):
        return [{"action": "noop"}]

    async def _execute_plan(self, plan, context):
        return [{"type": "result", "data": "found it"}]

    async def _reflect(self, findings, task, context):
        return AgentResult("Done", 0.9, [], status=AgentStatus.COMPLETED)


@pytest.mark.asyncio
async def test_llm_decompose_valid_json():
    """When LLM returns valid JSON with known roles, those tasks are used."""
    tasks_json = json.dumps([
        {"role": "researcher", "goal": "find stuff", "constraints": []},
        {"role": "auditor", "goal": "check stuff", "constraints": []}
    ])
    llm = _MockLLM(tasks_json)
    orch = Orchestrator({"researcher": _SimpleAgent, "auditor": _SimpleAgent}, llm_interface=llm)
    tasks = await orch.decompose_task("do something")
    assert len(tasks) == 2
    assert tasks[0]["role"] == "researcher"
    assert tasks[1]["role"] == "auditor"


@pytest.mark.asyncio
async def test_llm_decompose_markdown_fenced_json():
    """LLM response wrapped in markdown code fences should be parsed."""
    tasks_json = '```json\n' + json.dumps([
        {"role": "researcher", "goal": "find stuff", "constraints": []}
    ]) + '\n```'
    llm = _MockLLM(tasks_json)
    orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
    tasks = await orch.decompose_task("research this")
    assert len(tasks) == 1
    assert tasks[0]["role"] == "researcher"


@pytest.mark.asyncio
async def test_llm_decompose_unknown_roles_filtered():
    """Tasks with unknown roles should be filtered out."""
    tasks_json = json.dumps([
        {"role": "unknown_agent", "goal": "x", "constraints": []},
        {"role": "researcher", "goal": "y", "constraints": []}
    ])
    llm = _MockLLM(tasks_json)
    orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
    tasks = await orch.decompose_task("do it")
    assert len(tasks) == 1
    assert tasks[0]["role"] == "researcher"


@pytest.mark.asyncio
async def test_llm_decompose_all_unknown_falls_back_to_heuristic():
    """If all LLM roles are unknown, fall back to heuristic."""
    tasks_json = json.dumps([
        {"role": "nonexistent", "goal": "x", "constraints": []}
    ])
    llm = _MockLLM(tasks_json)
    orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
    tasks = await orch.decompose_task("research something")
    # Heuristic should fire for "research" keyword
    assert any(t["role"] == "researcher" for t in tasks)


@pytest.mark.asyncio
async def test_llm_decompose_invalid_json_falls_back():
    """Invalid JSON from LLM should fall back to heuristic."""
    llm = _MockLLM("This is not JSON at all")
    orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
    tasks = await orch.decompose_task("audit the graph")
    # Heuristic should handle "audit" keyword
    assert any(t["role"] == "auditor" or t["role"] == "researcher" for t in tasks)


@pytest.mark.asyncio
async def test_llm_decompose_exception_falls_back():
    """Exception during LLM call should fall back to heuristic."""
    llm = MagicMock()
    llm.complete.side_effect = RuntimeError("connection failed")
    orch = Orchestrator({"researcher": _SimpleAgent}, llm_interface=llm)
    tasks = await orch.decompose_task("find something")
    assert len(tasks) >= 1


@pytest.mark.asyncio
async def test_execute_agent_failure_returns_failed_result():
    """An agent that raises should produce a FAILED AgentResult."""
    orch = Orchestrator({"researcher": _FailingAgent}, llm_interface=None)
    result = await orch.run_goal("research this", {})

    # The failing agent should produce a FAILED finding
    assert result["orchestration_summary"]["agents_successful"] == 0
    assert any(f["status"] == AgentStatus.FAILED for f in result["agent_findings"])
