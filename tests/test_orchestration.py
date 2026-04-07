import os
import sys
import unittest
import asyncio

# Add the repo root to the path
repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, repo_path)

from application.orchestrator import Orchestrator
from infrastructure.llm_implementations import MockLLMInterface
from domain.core.agents_impl import ResearcherAgent, AuditorAgent

class TestOrchestration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_llm = MockLLMInterface()
        self.registry = {
            "researcher": ResearcherAgent,
            "auditor": AuditorAgent
        }
        self.orchestrator = Orchestrator(self.registry, self.mock_llm)

    async def test_goal_decomposition_and_execution(self):
        # Test a goal that triggers decomposition into 2 agents (audit triggers researcher + auditor)
        goal = "Audit my recent skill growth"
        result = await self.orchestrator.run_goal(goal, {})

        self.assertEqual(result["goal"], goal)
        self.assertEqual(result["orchestration_summary"]["agents_dispatched"], 2)
        self.assertEqual(len(result["agent_findings"]), 2)

    async def test_single_task_goal(self):
        # Test a simple goal that doesn't trigger decomposition (falls back to single researcher)
        goal = "What is the current zeitgeist?"
        result = await self.orchestrator.run_goal(goal, {})

        self.assertEqual(result["orchestration_summary"]["agents_dispatched"], 1)
        self.assertEqual(len(result["agent_findings"]), 1)

if __name__ == '__main__':
    unittest.main()
