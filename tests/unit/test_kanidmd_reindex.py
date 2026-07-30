"""Unit tests for kanidmd_reindex module."""

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
    spec = importlib.util.spec_from_file_location("kanidmd_reindex", "plugins/modules/kanidmd_reindex.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")
    assert hasattr(module, "DOCUMENTATION")


def test_documentation_structure():
    """Test that documentation has required fields."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_reindex", "plugins/modules/kanidmd_reindex.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    doc = yaml.safe_load(module.DOCUMENTATION)
    assert "module" in doc
    assert "options" in doc
    assert "kanidmd_binary" in doc["options"]
    assert "state" in doc["options"]


def test_module_returns_doc():
    """Test that module returns expected documentation structure."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_reindex", "plugins/modules/kanidmd_reindex.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Verify RETURN documentation exists
    assert "reindexed" in module.RETURN or "changed" in module.RETURN
