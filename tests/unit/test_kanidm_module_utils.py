#!/usr/bin/env python3
# Unit tests for kanidm module_utils

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins"))

from module_utils.kanidm import KanidmModuleMixin, _run_async, kanidm_argument_spec


class TestRunAsync:
    """Test _run_async helper."""

    def test_run_async_basic(self):
        """Test running an async function synchronously."""

        async def async_func():
            return "result"

        result = _run_async(async_func())
        assert result == "result"

    def test_run_async_with_exception(self):
        """Test that exceptions in async functions are propagated."""

        async def async_func():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            _run_async(async_func())

    def test_run_async_multiple_calls(self):
        """Test multiple sequential calls."""

        async def async_func(value):
            return value * 2

        result1 = _run_async(async_func(5))
        result2 = _run_async(async_func(10))
        assert result1 == 10
        assert result2 == 20


class TestKanidmArgumentSpec:
    """Test kanidm_argument_spec function."""

    def test_returns_dict(self):
        """Test that argument_spec returns a dictionary."""
        spec = kanidm_argument_spec()
        assert isinstance(spec, dict)

    def test_required_fields(self):
        """Test that required fields are present."""
        spec = kanidm_argument_spec()
        required_fields = ["server"]
        for field in required_fields:
            assert field in spec, f"Missing required field: {field}"

    def test_field_types(self):
        """Test field types are correct."""
        spec = kanidm_argument_spec()
        assert spec["server"]["type"] == "str"
        assert spec["session_token"]["type"] == "str"
        assert spec["username"]["type"] == "str"
        assert spec["password"]["type"] == "str"
        assert spec["password_env"]["type"] == "str"
        assert spec["kanidm_verify_tls"]["type"] == "bool"
        assert spec["kanidm_ca_path"]["type"] == "str"

    def test_no_log_fields(self):
        """Test that sensitive fields have no_log=True."""
        spec = kanidm_argument_spec()
        assert spec["session_token"]["no_log"] is True
        assert spec["password"]["no_log"] is True

    def test_default_values(self):
        """Test default values for optional fields."""
        spec = kanidm_argument_spec()
        assert spec["kanidm_verify_tls"]["default"] is True


class MockKanidmModule(KanidmModuleMixin):
    """Mock module for testing KanidmModuleMixin."""

    def __init__(self, params):
        # Pop kanidm-specific params before passing to super
        self._test_params = params.copy()
        kanidm_params = {k: params.pop(k) for k in ["kanidm_verify_tls", "kanidm_ca_path"] if k in params}
        super().__init__(**kanidm_params)
        # Store params as instance attrs for testing
        self.params = params

    def fail_json(self, **kwargs):
        raise Exception(f"fail_json: {kwargs}")

    def exit_json(self, **kwargs):
        pass

    def _set_variables(self, vars_dict):
        pass


class TestKanidmModuleMixin:
    """Test KanidmModuleMixin functionality."""

    @patch("module_utils.kanidm.kanidm")
    def test_build_client_with_token(self, mock_kanidm):
        """Test building client with session token."""
        mock_client = MagicMock()
        mock_kanidm.KanidmClient.return_value = mock_client

        params = {
            "server": "https://idm.example.com",
            "session_token": "test-token",
            "kanidm_verify_tls": True,
        }

        module = MockKanidmModule(params)
        client = module._build_client()

        assert client == mock_client
        mock_kanidm.KanidmClient.assert_called_once()
        config = mock_kanidm.KanidmClient.call_args[1]["config"]
        assert config.auth_token == "test-token"

    @patch("module_utils.kanidm.kanidm")
    def test_build_client_without_token(self, mock_kanidm):
        """Test building client without session token."""
        mock_client = MagicMock()
        mock_kanidm.KanidmClient.return_value = mock_client

        params = {
            "server": "https://idm.example.com",
            "kanidm_verify_tls": True,
        }

        module = MockKanidmModule(params)
        client = module._build_client()

        assert client == mock_client
        mock_kanidm.KanidmClient.assert_called_once()
        config = mock_kanidm.KanidmClient.call_args[1]["config"]
        assert config.auth_token is None

    def test_resolve_password_direct(self):
        """Test resolving password from direct parameter."""
        params = {"password": "test-password"}
        module = MockKanidmModule(params)
        password = module._resolve_password()
        assert password == "test-password"

    def test_resolve_password_env(self):
        """Test resolving password from environment variable."""
        params = {"password_env": "TEST_PASSWORD"}
        module = MockKanidmModule(params)

        with patch.dict("os.environ", {"TEST_PASSWORD": "env-password"}):
            password = module._resolve_password()
            assert password == "env-password"

    def test_resolve_password_fallback(self):
        """Test password resolution with no password available."""
        params = {}
        module = MockKanidmModule(params)
        password = module._resolve_password()
        assert password is None

    @patch("module_utils.kanidm.kanidm")
    @patch("module_utils.kanidm._run_async")
    def test_authenticate_with_token(self, mock_run_async, mock_kanidm):
        """Test authentication with existing token."""
        mock_run_async.return_value = True  # Token is valid

        params = {
            "server": "https://idm.example.com",
            "session_token": "test-token",
            "kanidm_verify_tls": True,
        }

        module = MockKanidmModule(params)
        token = module._authenticate()
        assert token == "test-token"

    @patch("module_utils.kanidm.kanidm")
    @patch("module_utils.kanidm._run_async")
    def test_authenticate_with_password(self, mock_run_async, mock_kanidm):
        """Test authentication with username/password."""
        # Mock the 3-step auth flow
        mock_init_response = MagicMock()
        mock_init_response.response.headers = {"x-kanidm-auth-session-id": "session-id"}

        mock_begin_response = MagicMock()

        mock_auth_state = MagicMock()
        mock_auth_state.state.success = "final-token"

        mock_run_async.side_effect = [mock_init_response, mock_begin_response, mock_auth_state]

        params = {
            "server": "https://idm.example.com",
            "username": "admin",
            "password": "password",
            "kanidm_verify_tls": True,
        }

        module = MockKanidmModule(params)
        token = module._authenticate()
        assert token == "final-token"

    @patch("module_utils.kanidm.kanidm")
    @patch("module_utils.kanidm._run_async")
    def test_authenticate_missing_credentials(self, mock_run_async, mock_kanidm):
        """Test authentication fails without credentials."""
        params = {"server": "https://idm.example.com"}
        module = MockKanidmModule(params)

        with pytest.raises(Exception, match="Either 'session_token' or both"):
            module._authenticate()

    @patch("module_utils.kanidm.kanidm")
    @patch("module_utils.kanidm._run_async")
    def test_authenticate_invalid_token(self, mock_run_async, mock_kanidm):
        """Test authentication fails with invalid token."""
        mock_run_async.return_value = False  # Token is invalid

        params = {
            "server": "https://idm.example.com",
            "session_token": "invalid-token",
            "kanidm_verify_tls": True,
        }

        module = MockKanidmModule(params)

        with pytest.raises(Exception, match="Session token is invalid"):
            module._authenticate()
