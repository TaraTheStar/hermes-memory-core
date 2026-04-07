# Re-export from the canonical domain port for backwards compatibility.
# All new code should import from domain.core.ports.llm_port directly.
from domain.core.ports.llm_port import BaseLLMInterface

__all__ = ["BaseLLMInterface"]
