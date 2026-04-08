import os
import tempfile
import pytest

from domain.supporting.config_loader import ConfigLoader

# Use a directory within the project root for temp config files so they pass
# the allowed-path validation.  The project root is an allowed directory.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEST_TMPDIR = os.path.join(_PROJECT_ROOT, ".test_tmp")
os.makedirs(_TEST_TMPDIR, exist_ok=True)


def test_missing_config_file_raises():
    """Missing config file should raise FileNotFoundError with helpful message."""
    with pytest.raises(FileNotFoundError, match="HERMES_CONFIG_PATH"):
        ConfigLoader(os.path.join(_TEST_TMPDIR, "hermes_nonexistent_config.yaml"))


def test_path_outside_allowlist_raises():
    """Config path outside allowed directories should raise ValueError."""
    with pytest.raises(ValueError, match="outside the allowed directories"):
        ConfigLoader("/nonexistent/path/config.yaml")


def test_valid_config_loads():
    """Valid YAML config should load successfully."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, dir=_TEST_TMPDIR) as f:
        f.write("delegation:\n  base_url: http://localhost:8080\n  api_key: test-key\n  model: test-model\n")
        f.flush()
        try:
            loader = ConfigLoader(f.name)
            config = loader.get_delegation_config()
            assert config["base_url"] == "http://localhost:8080"
            assert config["api_key"] == "test-key"
            assert config["model"] == "test-model"
        finally:
            os.unlink(f.name)


def test_missing_delegation_block_raises():
    """Config without delegation block should raise KeyError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, dir=_TEST_TMPDIR) as f:
        f.write("other_key: value\n")
        f.flush()
        try:
            loader = ConfigLoader(f.name)
            with pytest.raises(KeyError):
                loader.get_delegation_config()
        finally:
            os.unlink(f.name)


def test_invalid_yaml_raises():
    """Malformed YAML should raise RuntimeError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, dir=_TEST_TMPDIR) as f:
        # Use content that reliably triggers a YAML parse error
        f.write("key: [\n")
        f.flush()
        try:
            with pytest.raises(RuntimeError, match="Failed to parse"):
                ConfigLoader(f.name)
        finally:
            os.unlink(f.name)


def test_tmp_path_rejected():
    """Config paths under /tmp should be rejected after security hardening."""
    with pytest.raises(ValueError, match="outside the allowed directories"):
        ConfigLoader("/tmp/some_config.yaml")
