import yaml
import os
from typing import Dict, Any, Optional
from domain.core.acl.storage_translator import StorageTranslator

DEFAULT_CONFIG_PATH = os.environ.get('HERMES_CONFIG_PATH', '/opt/data/config.yaml')

class ConfigLoader:
    """
    Utility to load system-level configuration files.
    Ensures secrets are read from the environment/config at runtime,
    not hardcoded in the repository.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.translator = StorageTranslator()
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            # Use the translator to handle the exception
            try:
                raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
            except Exception as e:
                event = self.translator.translate_exception(e)
                print(f"[ACL] Caught Config Loading Exception: {event}")
                raise event
        
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            # Transform parsing errors through the ACL
            event = self.translator.translate_exception(e)
            print(f"[ACL] Caught Config Parsing Exception: {event}")
            raise event

    def get_delegation_config(self) -> Dict[str, Any]:
        """
        Retrieve the 'delegation' block containing LLM provider details.
        """
        delegation = self._config.get('delegation')
        if not delegation:
            raise KeyError("Missing 'delegation' configuration in config.yaml")
        return delegation

    def get_all(self) -> Dict[str, Any]:
        return self._config
