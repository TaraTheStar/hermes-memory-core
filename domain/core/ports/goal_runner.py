from typing import Protocol, Dict, Any

class GoalRunner(Protocol):
    """
    A protocol for any component capable of executing an autonomous goal.
    This allows the InsightTrigger to trigger investigations without 
    knowing the implementation details of the Orchestrator.
    """
    async def run_goal(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        ...
