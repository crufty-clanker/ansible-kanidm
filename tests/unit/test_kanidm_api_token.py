"""Unit tests for kanidm_api_token module."""

import json
import sys
from unittest.mock import MagicMock, patch
import yaml

import pytest

# Mock Ansible imports
sys.modules["ansible.module_utils.basic"] = MagicMock()


def test_module_compiles():
    """Test that the module file compiles without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidm_api_token", "plugins/modules/kanidm_api_token.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")
    assert hasattr(module, "DOCUMENTATION")
    assert hasattr(module, "EXAMPLES")
    assert hasattr(module, "RETURN")


def test_documentation_structure():
    """Test that documentation has required fields."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidm_api_token", "plugins/modules/kanidm_api_token.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    doc = yaml.safe_load(module.DOCUMENTATION)
    assert "module" in doc
    assert "options" in doc
    assert "server" in doc["options"]
    assert "session_token" in doc["options"]
    assert "account" in doc["options"]


def test_module_returns_doc():
    """Test that module returns expected documentation structure."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidm_api_token", "plugins/modules/kanidm_api_token.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Verify RETURN documentation exists
    assert "token" in module.RETURN or "token_id" in module.RETURN
