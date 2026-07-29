#!/usr/bin/env python3
# Unit tests for kanidm_group module

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.kanidm_group import _members_need_update


class MockGroup:
    """Mock Kanidm Group object."""

    def __init__(self, name, member=None, dynmember=None, uuid="test-uuid", spn="test@idm.example.com"):
        self.name = name
        self.member = member or []
        self.dynmember = dynmember or []
        self.uuid = uuid
        self.spn = spn


class TestMembersNeedUpdate:
    """Test _members_need_update helper."""

    def test_same_members(self):
        """Test that identical member lists return False."""
        assert _members_need_update(["alice", "bob"], ["bob", "alice"]) is False

    def test_different_members(self):
        """Test that different member lists return True."""
        assert _members_need_update(["alice", "bob"], ["alice", "charlie"]) is True

    def test_empty_lists(self):
        """Test that empty lists are equal."""
        assert _members_need_update([], []) is False

    def test_subset(self):
        """Test subset comparison."""
        assert _members_need_update(["alice", "bob"], ["alice"]) is True
        assert _members_need_update(["alice"], ["alice", "bob"]) is True

    def test_single_member(self):
        """Test single member comparison."""
        assert _members_need_update(["alice"], ["alice"]) is False
        assert _members_need_update(["alice"], ["bob"]) is True
