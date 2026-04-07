import asyncio
import logging
from typing import Dict, Any, List, Optional, Type
from application.orchestrator import Orchestrator
from domain.core.agent import HermesAgent, AgentStatus
from domain.core.ports import GoalRunner
from domain.core.semantic_memory import SemanticMemory
from domain.supporting.ledger import StructuralLedger

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AutonomousOrchestrator")

class AutonomousOrchestrator(Orchestrator, GoalRunner):
    """
    An extension of the Orchestrator that can initiate its own investigation goals
    based on environmental stimuli (anomalies, new memory, structural changes).
    """
    def __init__(self, registry: Dict[str, Type[HermesAgent]], llm_interface=None, 
                 semantic_memory: Optional[SemanticMemory] = None,
                 structural_ledger: Optional[StructuralLedger] = None):
        super().__init__(registry, llm_interface)
        self.semantic_memory = semantic_memory
        self.structural_ledger = structural_ledger
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start_monitoring(self, interval_seconds: int = 300, context: Dict[str, Any] = None):
        """Starts the background monitoring loop."""
        if self._is_running:
            logger.warning("Monitoring is already running.")
            return

        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds, context or {}))
        logger.info(f"Autonomous monitoring started with {interval_seconds}s interval.")

    async def stop_monitoring(self):
        """Stops the background monitoring loop."""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Autonomous monitoring stopped.")

    async def _monitoring_loop(self, interval_seconds: int, context: Dict[str, Any]):
        """The core loop of the autonomous agent."""
        while self._is_running:
            try:
                logger.info("Scanning environment for triggers...")
                
                # 1. Check for new semantic intelligence
                if self.semantic_memory:
                    # In a real system, we'd use a more sophisticated 'has_new_events' check
                    # Here we just simulate finding an interesting recent event
                    recent_events = self.semantic_memory.list_events(limit=5)
                    if recent_events:
                        # For demonstration: trigger a goal if a specific keyword appears
                        for event in recent_events:
                            if "milestone" in event['metadata'].get('type', '') or "integration" in event['text'].lower():
                                goal = f"Investigate the recent semantic milestone: {event['text']}"
                                logger.info(f"Trigger detected! New Goal: {goal}")
                                await self.run_goal(goal, context)
                                break

                # 2. Check for structural changes
                if self.structural_ledger:
                    # Simulate a structural anomaly check
                    # In a real system, this would query the ledger for recent additions/deletions
                    pass

                # Wait for the next interval
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds) # Avoid rapid-fire error loops

    async def run_goal(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of the GoalRunner protocol.
        Extends run_goal to include autonomous-specific logging.
        """
        logger.info(f"🚀 EXECUTING AUTONOMOUS GOAL: {goal}")
        result = await super().run_goal(goal, context)
        logger.info(f"✅ AUTONOMOUS GOAL COMPLETED. Confidence: {result.get('orchestration_summary', {}).get('aggregate_confidence', 0)}")
        return result

if __name__ == "__main__":
    async def test_loop():
        import os
        import shutil
        from domain.core.agents_impl import ResearcherAgent, AuditorAgent
        from domain.core.semantic_memory import SemanticMemory
        from domain.supporting.ledger import StructuralLedger
        from domain.core.ports import BaseLLMInterface
        
        class MockLLM(BaseLLMInterface):
            def complete(self, prompt: str, system_prompt: str = None) -> str:
                return "Simulated research findings."

        test_dir = '/tmp/autonomy_test'
        if os.path.exists(test_dir): shutil.rmtree(test_dir)
        os.makedirs(test_dir)

        sm = SemanticMemory(persist_directory=test_dir)
        sl = StructuralLedger(test_dir)
        
        registry = {"researcher": ResearcherAgent, "auditor": AuditorAgent}
        mock_llm = MockLLM()
        orch = AutonomousOrchestrator(registry, mock_llm, semantic_memory=sm, structural_ledger=sl)

        # Seed an event that should trigger the monitor
        sm.add_event("Major integration milestone achieved!", {"type": "milestone"}, context_id="dev")

        # Start monitoring with a short interval for testing
        await orch.start_monitoring(interval_seconds=5, context={"semantic_memory": sm, "context_id": "dev"})
        
        print("Monitoring running... (will run for 15 seconds)")
        await asyncio.sleep(15)
        await orch.stop_monitoring()

    asyncio.run(test_loop())
