"""Tests for RefinementRegistry input validation."""
import pytest
from unittest.mock import MagicMock
from domain.core.refinement_registry import RefinementRegistry


def _make_proposal(target="researcher_prompt", state="Be more concise."):
    p = MagicMock()
    p.target_component = target
    p.proposed_state = state
    return p


def test_apply_valid_proposal():
    reg = RefinementRegistry()
    reg.apply(_make_proposal())
    assert reg.get_refinement("researcher_prompt") == "Be more concise."


def test_apply_rejects_non_string_target():
    reg = RefinementRegistry()
    reg.apply(_make_proposal(target=None))
    assert reg.get_all() == {}


def test_apply_rejects_empty_target():
    reg = RefinementRegistry()
    reg.apply(_make_proposal(target="  "))
    assert reg.get_all() == {}


def test_apply_rejects_non_string_value():
    reg = RefinementRegistry()
    p = _make_proposal()
    p.proposed_state = {"nested": "dict"}
    reg.apply(p)
    assert reg.get_all() == {}


def test_apply_rejects_oversized_value():
    reg = RefinementRegistry()
    reg.apply(_make_proposal(state="x" * 6000))
    assert reg.get_all() == {}


def test_apply_accepts_max_length_value():
    reg = RefinementRegistry()
    value = "x" * 5000
    reg.apply(_make_proposal(state=value))
    assert reg.get_refinement("researcher_prompt") == value
