import os
import shutil
import pytest

from domain.core.semantic_memory import SemanticMemory
from domain.core.acl.llm_translator import LLMTranslator
from domain.core.events import InfrastructureErrorEvent, EventSeverity


@pytest.fixture
def test_dir(tmp_path):
    d = tmp_path / "semantic_v3"
    d.mkdir()
    return str(d)


def test_semantic_context_isolation(test_dir):
    """Events in one context should not leak into queries for another context."""
    sm = SemanticMemory(persist_directory=test_dir)

    sm.add_event("marketing_secret_alpha", {"type": "msg"}, context_id="marketing")
    sm.add_event("core_stability_beta", {"type": "msg"}, context_id="core")

    # Query marketing context for marketing keyword — should find it
    m_results = sm.query("marketing_secret_alpha", context_id="marketing")
    assert len(m_results) > 0

    # Query core context for marketing keyword — should NOT find it
    c_results_for_m = sm.query("marketing_secret_alpha", context_id="core")
    assert len(c_results_for_m) == 0, (
        f"Context isolation failed — leaked events: "
        f"{[r['metadata'].get('context_id') for r in c_results_for_m]}"
    )


def test_acl_transformation():
    """LLMTranslator should convert exceptions into InfrastructureErrorEvents."""
    translator = LLMTranslator()
    try:
        raise ConnectionError("Connection refused by remote server")
    except Exception as e:
        event = translator.translate_exception(e)

    assert isinstance(event, InfrastructureErrorEvent)
    assert event.severity == EventSeverity.ERROR
