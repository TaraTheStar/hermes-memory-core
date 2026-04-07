from typing import Any, Optional
from domain.core.acl.base import BaseTranslator
from domain.core.events import InfrastructureErrorEvent, EventSeverity

class LLMTranslator(BaseTranslator):
    """
    Translator for LLM-related exceptions.
    Converts technical API errors (OpenAI, connection errors, etc.) 
    into semantic InfrastructureErrorEvent domain events.
    """

    def translate_exception(self, exception: Exception) -> InfrastructureErrorEvent:
        error_msg = str(exception)
        severity = EventSeverity.ERROR
        error_code = "LLM_API_FAILURE"

        # Specific mapping for common LLM errors
        if "AuthenticationError" in error_msg or "api_key" in error_msg.lower():
            severity = EventSeverity.CRITICAL
            error_code = "LLM_AUTH_FAILURE"
        elif "RateLimitError" in error_msg or "429" in error_msg:
            severity = EventSeverity.WARNING
            error_code = "LLM_RATE_LIMIT"
        elif "ConnectionError" in error_msg or "timeout" in error_msg.lower():
            severity = EventSeverity.ERROR
            error_code = "LLM_CONNECTION_TIMEOUT"
        elif "InvalidRequestError" in error_msg or "400" in error_msg:
            severity = EventSeverity.ERROR
            error_code = "LLM_INVALID_REQUEST"

        return InfrastructureErrorEvent(
            severity=severity,
            source="LLM_Infrastructure",
            error_code=error_code,
            original_exception=error_msg,
            metadata={"exception_type": type(exception).__name__}
        )

    def transform_data(self, raw_data: Any) -> Any:
        """
        For LLM, data transformation might involve cleaning whitespace 
        or verifying the structure of a JSON response.
        """
        if isinstance(raw_data, str):
            return raw_data.strip()
        return raw_data
