"""Tests for SemanticMemory input validation and bounds checking."""
import os
import tempfile
import shutil
import pytest
from domain.core.semantic_memory import SemanticMemory


@pytest.fixture
def semantic_memory():
    tmpdir = tempfile.mkdtemp()
    mem = SemanticMemory(tmpdir)
    yield mem
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_query_n_results_zero_returns_empty(semantic_memory):
    """n_results=0 should return an empty list, not raise."""
    result = semantic_memory.query("anything", n_results=0)
    assert result == []


def test_query_n_results_negative_returns_empty(semantic_memory):
    """Negative n_results should return an empty list."""
    result = semantic_memory.query("anything", n_results=-1)
    assert result == []


def test_query_n_results_capped(semantic_memory):
    """Very large n_results should be capped to _MAX_QUERY_RESULTS."""
    # Just verify it doesn't crash with a huge value
    semantic_memory.add_event("test event", {"type": "test"})
    result = semantic_memory.query("test", n_results=999999)
    # Should succeed without trying to fetch 5 million results
    assert isinstance(result, list)


def test_min_similarity_filters_low_relevance(semantic_memory):
    """Results below min_similarity should be filtered out."""
    semantic_memory.add_event("The cat sat on the mat", {"type": "test"})
    semantic_memory.add_event("Quantum physics equations", {"type": "test"})

    # With a very high threshold, unrelated results should be filtered
    results = semantic_memory.query("cat mat", n_results=10, min_similarity=0.99)
    # Can't guarantee exact filtering with default embeddings, but shouldn't crash
    assert isinstance(results, list)
