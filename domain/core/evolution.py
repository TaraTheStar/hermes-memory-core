import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class EvolutionType(str, Enum):
    SKILL_ACQUISITION = "skill_acquisition"  # New workflow discovered
    ESSENCE_SHIFT = "essence_shift"          # New fundamental truth about self/purpose
    PATTERN_RECOGNITION = "pattern_recognition" # New structural insight
    REFINEMENT = "refinement"                # Optimization of an existing process

class EvolutionEvent(BaseModel):
    """
    A discrete moment of growth discovered by the agent.
    """
    event_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    evolution_type: EvolutionType
    summary: str
    evidence: Dict[str, Any]  # Links to tool outputs, logs, or decision traces
    impact_score: float = Field(ge=0.0, le=1.0)

class EvolutionManifest(BaseModel):
    """
    The formal proposal for updating the agent's core identity or capabilities.
    """
    event: EvolutionEvent
    target_file: str  # e.g., "SOUL.md" or "skills/new_skill.md"
    proposed_changes: str # The actual text/code to be injected/patched
    validation_criteria: List[str] # How to verify the update worked
