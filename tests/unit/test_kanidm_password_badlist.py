"""Unit tests for kanidm_password_badlist module."""

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
    spec = importlib.util.spec_from_file_location("kanidm_password_badlist", "plugins/modules/kanidm_password_badlist.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")
    assert hasattr(module, "DOCUMENTATION")


def test_documentation_structure():
    """Test that documentation has required fields."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidm_password_badlist", "plugins/modules/kanidm_password_badlist.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    doc = yaml.safe_load(module.DOCUMENTATION)
    assert "module" in doc
    assert "options" in doc
    assert "server" in doc["options"]
    assert "passwords" in doc["options"]
    assert "state" in doc["options"]


def test_module_returns_doc():
    """Test that module returns expected documentation structure."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidm_password_badlist", "plugins/modules/kanidm_password_badlist.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Verify RETURN documentation exists
    assert "changed" in module.RETURN or "added" in module.RETURN
