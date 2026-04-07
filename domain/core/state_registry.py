from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, field

@dataclass
class StateEntry:
    """Represents a single piece of state within a context."""
    value: Any
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

class StateRegistry:
    """
    A centralized, context-aware registry for managing the operational state
    of the Hermes Memory Engine across different Bounded Contexts.
    """
    def __init__(self):
        # Structure: { context_id: { key: StateEntry } }
        self._registry: Dict[str, Dict[str, StateEntry]] = {}
        # Global context for non-domain specific state
        self.GLOBAL_CONTEXT = "global"

    def set_state(self, key: str, value: Any, context_id: str = "global", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Sets a state value within a specific Bounded Context.
        """
        if context_id not in self._registry:
            self._registry[context_id] = {}
        
        self._registry[context_id][key] = StateEntry(
            value=value,
            metadata=metadata or {}
        )

    def get_state(self, key: str, context_id: str = "global") -> Optional[Any]:
        """
        Retrieves a state value from a specific Bounded Context.
        """
        context_map = self._registry.get(context_id)
        if context_map and key in context_map:
            return context_map[key].value
        return None

    def get_all_in_context(self, context_id: str) -> Dict[str, Any]:
        """
        Returns the entire state dictionary for a given context.
        """
        context_map = self._registry.get(context_id, {})
        return {k: v.value for k, v in context_map.items()}

    def delete_state(self, key: str, context_id: str = "global") -> bool:
        """
        Removes a specific key from a context.
        """
        if context_id in self._registry and key in self._registry[context_id]:
            del self._registry[context_id][key]
            return True
        return False

    def clear_context(self, context_id: str) -> None:
        """
        Wipes all state associated with a specific context.
        """
        if context_id in self._registry:
            del self._registry[context_id]

    def list_contexts(self) -> List[str]:
        """
        Returns a list of all active Bounded Contexts in the registry.
        """
        return list(self._registry.keys())
