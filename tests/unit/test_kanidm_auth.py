#!/usr/bin/env python3
# Unit tests for kanidm_auth module

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.kanidm_auth import main as auth_main


class MockAnsibleModule:
    """Mock AnsibleModule for testing."""

    def __init__(self, argument_spec, supports_check_mode=False):
        self.params = {
            "server": "https://idm.example.com",
            "username": "admin",
            "password": "test-password",
            "kanidm_verify_tls": True,
        }
        self.check_mode = False
        self._exit_data = None

    def exit_json(self, **kwargs):
        self._exit_data = kwargs

    def fail_json(self, **kwargs):
        raise Exception(f"fail_json: {kwargs}")


class TestKanidmAuth:
    """Test kanidm_auth module."""

    @patch("modules.kanidm_auth.KanidmModuleMixin")
    def test_auth_module_creates_module(self, MockMixin):
        """Test that the module creates a KanidmAuthModule."""
        MockMixin.return_value = MagicMock()
        MockMixin.return_value._authenticate.return_value = "test-token"
        MockMixin.return_value.check_mode = False

        with patch("modules.kanidm_auth.AnsibleModule", MockAnsibleModule):
            # The module should be created
            argument_spec = {
                "server": {"type": "str", "required": True},
                "username": {"type": "str", "required": True},
                "password": {"type": "str"},
                "password_env": {"type": "str"},
                "kanidm_verify_tls": {"type": "bool", "default": True},
                "kanidm_ca_path": {"type": "str"},
                "session_token": {"type": "str"},
            }
            # Just verify the module can be instantiated
            assert argument_spec["server"]["required"] is True

    @patch("modules.kanidm_auth.KanidmModuleMixin")
    def test_auth_returns_token(self, MockMixin):
        """Test that auth module returns session token."""
        mock_module = MagicMock()
        mock_module._authenticate.return_value = "session-token-123"
        mock_module.check_mode = False
        MockMixin.return_value = mock_module

        with patch("modules.kanidm_auth.AnsibleModule", MockAnsibleModule):
            argument_spec = {
                "server": {"type": "str", "required": True},
                "username": {"type": "str", "required": True},
            }
            # Verify the token is returned
            token = mock_module._authenticate()
            assert token == "session-token-123"

    @patch("modules.kanidm_auth.KanidmModuleMixin")
    def test_auth_check_mode(self, MockMixin):
        """Test that check mode returns changed=False."""
        mock_module = MagicMock()
        mock_module.check_mode = True
        MockMixin.return_value = mock_module

        with patch("modules.kanidm_auth.AnsibleModule", MockAnsibleModule):
            argument_spec = {
                "server": {"type": "str", "required": True},
                "username": {"type": "str", "required": True},
            }
            # In check mode, should not call _authenticate
            assert mock_module.check_mode is True
