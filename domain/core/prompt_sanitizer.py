"""
Sanitization utilities for untrusted data interpolated into LLM prompts.

Wraps user-controlled content in XML-style delimiters so the model can
distinguish system instructions from data, and caps the length to prevent
prompt stuffing.
"""

_MAX_FIELD_LENGTH = 2000


def sanitize_field(value: str, tag: str, max_length: int = _MAX_FIELD_LENGTH) -> str:
    """Wrap *value* in ``<tag>...</tag>`` delimiters after length-capping.

    Any embedded closing tags (``</tag>``) in *value* are escaped so the
    delimiter boundary cannot be spoofed.
    """
    text = str(value) if value is not None else ""
    if len(text) > max_length:
        text = text[:max_length] + "... [truncated]"
    text = text.replace(f"</{tag}>", f"<\\/{tag}>")
    return f"<{tag}>{text}</{tag}>"
