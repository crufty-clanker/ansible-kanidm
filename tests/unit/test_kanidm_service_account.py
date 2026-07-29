#!/usr/bin/env python3
# Unit tests for kanidm_service_account module

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.kanidm_service_account import _service_account_info


class MockServiceAccount:
    """Mock Kanidm ServiceAccount object."""

    def __init__(self, name, displayname="", memberof=None, spn="test@idm.example.com",
                 uuid="test-uuid", classes=None):
        self.name = name
        self.displayname = displayname
        self.memberof = memberof or []
        self.spn = spn
        self.uuid = uuid
        self.classes = classes or []


class TestServiceAccountInfo:
    """Test _service_account_info helper."""

    def test_sa_info_conversion(self):
        """Test converting ServiceAccount object to dict."""
        sa = MockServiceAccount(
            name="backup-agent",
            displayname="Backup Agent",
            memberof=["backup-group"],
            spn="backup-agent@idm.example.com",
            uuid="123e4567-e89b-12d3-a456-426614174000",
            classes=["service_account"],
        )

        info = _service_account_info(sa)
        assert info["name"] == "backup-agent"
        assert info["displayname"] == "Backup Agent"
        assert info["memberof"] == ["backup-group"]
        assert info["spn"] == "backup-agent@idm.example.com"
        assert info["uuid"] == "123e4567-e89b-12d3-a456-426614174000"
        assert info["classes"] == ["service_account"]

    def test_sa_info_minimal(self):
        """Test converting minimal ServiceAccount object."""
        sa = MockServiceAccount(name="minimal-sa")
        info = _service_account_info(sa)
        assert info["name"] == "minimal-sa"
        assert info["displayname"] == ""
        assert info["memberof"] == []
