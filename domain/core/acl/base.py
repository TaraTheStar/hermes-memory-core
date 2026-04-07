from abc import ABC, abstractmethod
from typing import Type, Optional, Any
from domain.core.events import DomainEvent

class BaseTranslator(ABC):
    """
    Abstract base class for all Anti-Corruption Layer translators.
    
    The purpose of a translator is to intercept low-level technical 
    exceptions or data structures and transform them into clean, 
    semantic DomainEvents or Domain Objects.
    """

    @abstractmethod
    def translate_exception(self, exception: Exception) -> DomainEvent:
        """
        Converts a technical exception into a structured DomainEvent.
        """
        pass

    @abstractmethod
    def transform_data(self, raw_data: Any) -> Any:
        """
        Converts raw, external data structures into clean Domain objects.
        """
        pass
