"""Unit tests for existing kanidmd modules (backup, restore, reload, verify, domain, healthcheck, disable_account, recover_account)."""

import json
import sys
from unittest.mock import MagicMock, patch
import yaml

import pytest

# Mock Ansible imports
sys.modules["ansible.module_utils.basic"] = MagicMock()


def test_kanidmd_backup_compiles():
    """Test that kanidmd_backup module compiles without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_backup", "plugins/modules/kanidmd_backup.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")
    assert hasattr(module, "DOCUMENTATION")


def test_kanidmd_backup_documentation():
    """Test kanidmd_backup documentation structure."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_backup", "plugins/modules/kanidmd_backup.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Just verify DOCUMENTATION exists and is not empty
    assert hasattr(module, "DOCUMENTATION")
    assert len(module.DOCUMENTATION) > 0
    # Check that key elements are present in the raw string
    assert "module: kanidmd_backup" in module.DOCUMENTATION
    assert "path" in module.DOCUMENTATION


def test_kanidmd_restore_compiles():
    """Test that kanidmd_restore module compiles without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_restore", "plugins/modules/kanidmd_restore.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_kanidmd_reload_compiles():
    """Test that kanidmd_reload module compiles without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_reload", "plugins/modules/kanidmd_reload.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_kanidmd_verify_compiles():
    """Test that kanidmd_verify module compiles without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_verify", "plugins/modules/kanidmd_verify.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_kanidmd_domain_compiles():
    """Test that kanidmd_domain module compiles without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_domain", "plugins/modules/kanidmd_domain.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_kanidmd_healthcheck_compiles():
    """Test that kanidmd_healthcheck module compiles without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_healthcheck", "plugins/modules/kanidmd_healthcheck.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_kanidmd_disable_account_compiles():
    """Test that kanidmd_disable_account module compiles without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_disable_account", "plugins/modules/kanidmd_disable_account.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_kanidmd_recover_account_compiles():
    """Test that kanidmd_recover_account module compiles without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("kanidmd_recover_account", "plugins/modules/kanidmd_recover_account.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")
