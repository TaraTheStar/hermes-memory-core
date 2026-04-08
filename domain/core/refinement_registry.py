from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RefinementRegistry:
    """
    A persistent registry of approved refinements (prompts, tool configs, etc.)
    that agents can query to evolve their behavior dynamically.
    """
    def __init__(self):
        self._refinements: Dict[str, Any] = {}

    # Maximum length for a proposed_state value stored in the registry.
    _MAX_VALUE_LENGTH = 5000

    def apply(self, proposal: Any) -> None:
        """Applies an approved refinement proposal to the registry after validation."""
        target = proposal.target_component
        value = proposal.proposed_state

        if not isinstance(target, str) or not target.strip():
            logger.warning("Rejected refinement: target_component must be a non-empty string, got %r", target)
            return
        if not isinstance(value, str):
            logger.warning("Rejected refinement: proposed_state must be a string, got %s", type(value).__name__)
            return
        if len(value) > self._MAX_VALUE_LENGTH:
            logger.warning("Rejected refinement: proposed_state exceeds %d chars (%d)", self._MAX_VALUE_LENGTH, len(value))
            return

        logger.info("Applying refinement to '%s': %s", target, value[:200])
        self._refinements[target] = value

    def get_refinement(self, target: str) -> Optional[Any]:
        """Retrieves a refinement for a specific target component."""
        return self._refinements.get(target)

    def get_all(self) -> Dict[str, Any]:
        """Returns all currently active refinements."""
        return self._refinements.copy()

# Singleton instance for easy access within the session
registry = RefinementRegistry()
