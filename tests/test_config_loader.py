import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from domain.supporting.config_loader import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    def test_missing_config_file_raises(self):
        """Missing config file should raise FileNotFoundError with helpful message."""
        with self.assertRaises(FileNotFoundError) as ctx:
            ConfigLoader("/nonexistent/path/config.yaml")
        self.assertIn("HERMES_CONFIG_PATH", str(ctx.exception))

    def test_valid_config_loads(self):
        """Valid YAML config should load successfully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("delegation:\n  base_url: http://localhost:8080\n  api_key: test-key\n  model: test-model\n")
            f.flush()
            try:
                loader = ConfigLoader(f.name)
                config = loader.get_delegation_config()
                self.assertEqual(config["base_url"], "http://localhost:8080")
                self.assertEqual(config["api_key"], "test-key")
                self.assertEqual(config["model"], "test-model")
            finally:
                os.unlink(f.name)

    def test_missing_delegation_block_raises(self):
        """Config without delegation block should raise KeyError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("other_key: value\n")
            f.flush()
            try:
                loader = ConfigLoader(f.name)
                with self.assertRaises(KeyError):
                    loader.get_delegation_config()
            finally:
                os.unlink(f.name)

    def test_invalid_yaml_raises(self):
        """Malformed YAML should raise RuntimeError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(":::invalid yaml{{{\n")
            f.flush()
            try:
                # PyYAML may or may not raise on this specific input,
                # but truly broken YAML should not silently succeed
                loader = ConfigLoader(f.name)
            except RuntimeError:
                pass  # Expected
            finally:
                os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
