"""Tests for infrastructure/paths.py path resolution."""
import os
import pytest
from unittest.mock import patch
from infrastructure.paths import _base_dir, default_structural_db, default_semantic_dir, _LOCAL_BASE


class TestBaseDir:
    def test_explicit_env_var_takes_precedence(self):
        with patch.dict(os.environ, {"HERMES_DATA_DIR": "/custom/path"}, clear=False):
            assert _base_dir() == "/custom/path"

    def test_docker_path_when_exists(self, tmp_path):
        docker_path = str(tmp_path / "docker_data")
        os.makedirs(docker_path)
        with patch.dict(os.environ, {}, clear=False):
            # Remove HERMES_DATA_DIR if set
            os.environ.pop("HERMES_DATA_DIR", None)
            with patch("infrastructure.paths._DOCKER_BASE", docker_path):
                assert _base_dir() == docker_path

    def test_local_fallback(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HERMES_DATA_DIR", None)
            with patch("infrastructure.paths._DOCKER_BASE", "/nonexistent_docker_path_12345"):
                assert _base_dir() == _LOCAL_BASE


class TestDefaultStructuralDb:
    def test_env_var_override(self):
        with patch.dict(os.environ, {"HERMES_STRUCTURAL_DB": "/my/db.sqlite"}, clear=False):
            assert default_structural_db() == "/my/db.sqlite"

    def test_default_uses_base_dir(self):
        with patch.dict(os.environ, {"HERMES_DATA_DIR": "/test_base"}, clear=False):
            os.environ.pop("HERMES_STRUCTURAL_DB", None)
            result = default_structural_db()
            assert result == "/test_base/structural/structure.db"


class TestDefaultSemanticDir:
    def test_env_var_override(self):
        with patch.dict(os.environ, {"HERMES_SEMANTIC_DIR": "/my/chroma"}, clear=False):
            assert default_semantic_dir() == "/my/chroma"

    def test_default_uses_base_dir(self):
        with patch.dict(os.environ, {"HERMES_DATA_DIR": "/test_base"}, clear=False):
            os.environ.pop("HERMES_SEMANTIC_DIR", None)
            result = default_semantic_dir()
            assert result == "/test_base/semantic/chroma_db"
