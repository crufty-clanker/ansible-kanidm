#!/usr/bin/env python3
# Unit tests for kanidmd modules

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from module_utils.kanidmd import KanidmdModuleMixin, kanidmd_argument_spec


class MockKanidmdModule(KanidmdModuleMixin):
    """Mock module for testing KanidmdModuleMixin."""

    def __init__(self, params):
        self._test_params = params.copy()
        kanidmd_params = {k: params.pop(k) for k in ["kanidmd_binary", "kanidmd_config_path", "kanidmd_db_path", "kanidmd_domain", "kanidmd_run_as_user"] if k in params}
        super().__init__(**kanidmd_params)
        self.params = params
        self._run_command_results = {}

    def fail_json(self, **kwargs):
        raise Exception(f"fail_json: {kwargs}")

    def exit_json(self, **kwargs):
        pass

    def run_command(self, args, check_rc=False):
        """Mock run_command that returns predefined results."""
        cmd_str = " ".join(args)
        if cmd_str in self._run_command_results:
            return self._run_command_results[cmd_str]
        # Default: return success for version command
        if args[-1] == "version":
            return (0, "kanidmd 1.10.4\n", "")
        return (0, "", "")


class TestKanidmdArgumentSpec:
    """Test kanidmd_argument_spec function."""

    def test_returns_dict(self):
        spec = kanidmd_argument_spec()
        assert isinstance(spec, dict)

    def test_required_fields(self):
        spec = kanidmd_argument_spec()
        assert "kanidmd_binary" in spec
        assert "kanidmd_config_path" in spec
        assert "kanidmd_db_path" in spec
        assert "kanidmd_domain" in spec

    def test_default_binary(self):
        spec = kanidmd_argument_spec()
        assert spec["kanidmd_binary"]["default"] == "kanidmd"


class TestKanidmdModuleMixin:
    """Test KanidmdModuleMixin functionality."""

    def test_build_kanidmd_args_basic(self):
        params = {}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["database", "backup"])
        assert args == ["kanidmd", "database", "backup"]

    def test_build_kanidmd_args_reload(self):
        params = {}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["scripting", "reload"])
        assert args == ["kanidmd", "scripting", "reload"]

    def test_build_kanidmd_args_verify(self):
        params = {}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["database", "verify"])
        assert args == ["kanidmd", "database", "verify"]

    def test_build_kanidmd_args_restore(self):
        params = {}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["database", "restore", "/backup/path"])
        assert args == ["kanidmd", "database", "restore", "/backup/path"]

    def test_build_kanidmd_args_with_config(self):
        params = {"kanidmd_config_path": "/etc/kanidm/config.toml"}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["domain", "show"])
        assert args == ["kanidmd", "-c", "/etc/kanidm/config.toml", "domain", "show"]

    def test_build_kanidmd_args_with_db_path(self):
        params = {"kanidmd_db_path": "/var/lib/kanidm"}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["database", "verify"])
        assert args == ["kanidmd", "--db-path", "/var/lib/kanidm", "database", "verify"]

    def test_build_kanidmd_args_with_domain(self):
        params = {"kanidmd_domain": "idm.example.com"}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["domain", "show"])
        assert args == ["kanidmd", "--domain", "idm.example.com", "domain", "show"]

    def test_build_kanidmd_args_custom_binary(self):
        params = {"kanidmd_binary": "/opt/kanidm/bin/kanidmd"}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["version"])
        assert args == ["/opt/kanidm/bin/kanidmd", "version"]

    def test_parse_json_output_valid(self):
        params = {}
        module = MockKanidmdModule(params)
        result = module._parse_json_output('{"name": "test"}')
        assert result == {"name": "test"}

    def test_parse_json_output_invalid(self):
        params = {}
        module = MockKanidmdModule(params)
        result = module._parse_json_output("not json")
        assert result is None

    def test_parse_json_output_empty(self):
        params = {}
        module = MockKanidmdModule(params)
        result = module._parse_json_output("")
        assert result is None

    @patch.object(MockKanidmdModule, "run_command")
    def test_ensure_kanidmd_available(self, mock_run_command):
        mock_run_command.return_value = (0, "kanidmd 1.10.4\n", "")
        params = {}
        module = MockKanidmdModule(params)
        assert module._ensure_kanidmd_available() is True

    @patch.object(MockKanidmdModule, "run_command")
    def test_ensure_kanidmd_not_available(self, mock_run_command):
        mock_run_command.return_value = (1, "", "command not found")
        params = {}
        module = MockKanidmdModule(params)
        assert module._ensure_kanidmd_available() is False

    def test_run_kanidmd_check_mode(self):
        params = {}
        module = MockKanidmdModule(params)
        rc, stdout, stderr = module._run_kanidmd(["version"], check_mode=True)
        assert rc == 0
        assert stdout == ""
        assert stderr == ""

    def test_run_kanidmd_actual(self):
        params = {}
        module = MockKanidmdModule(params)
        module._run_command_results["kanidmd domain show"] = (0, '{"name": "test"}', "")
        rc, stdout, stderr = module._run_kanidmd(["domain", "show"])
        assert rc == 0
        assert stdout == '{"name": "test"}'
        assert stderr == ""

    def test_build_kanidmd_args_vacuum(self):
        params = {}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["database", "vacuum"])
        assert args == ["kanidmd", "database", "vacuum"]

    def test_build_kanidmd_args_reindex(self):
        params = {}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["database", "reindex"])
        assert args == ["kanidmd", "database", "reindex"]

    def test_build_kanidmd_args_configtest(self):
        params = {}
        module = MockKanidmdModule(params)
        args = module._build_kanidmd_args(["configtest"])
        assert args == ["kanidmd", "configtest"]
