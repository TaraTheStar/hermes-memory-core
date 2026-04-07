from abc import ABC, abstractmethod
from typing import Optional

class BaseLLMInterface(ABC):
    """
    An abstract interface (domain port) for interacting with Large Language Models.
    Lives in the domain layer so domain components can depend on it
    without importing from infrastructure.
    """

    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Sends a prompt to the LLM and returns the generated text.

        Args:
            prompt: The user/task prompt.
            system_prompt: An optional system instruction to set the persona/context.

        Returns:
            The LLM's response as a string.
        """
        pass
