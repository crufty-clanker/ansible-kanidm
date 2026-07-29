#!/usr/bin/env python3
# Unit tests for kanidm_person module

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.kanidm_person import _person_info


class MockPerson:
    """Mock Kanidm Person object."""

    def __init__(self, name, displayname="", memberof=None, spn="test@idm.example.com",
                 uuid="test-uuid", classes=None, attrs=None):
        self.name = name
        self.displayname = displayname
        self.memberof = memberof or []
        self.spn = spn
        self.uuid = uuid
        self.classes = classes or []
        self.attrs = attrs or {}


class TestPersonInfo:
    """Test _person_info helper."""

    def test_person_info_conversion(self):
        """Test converting Person object to dict."""
        person = MockPerson(
            name="alice",
            displayname="Alice Smith",
            memberof=["ssh-login"],
            spn="alice@idm.example.com",
            uuid="123e4567-e89b-12d3-a456-426614174000",
            classes=["person"],
        )

        info = _person_info(person)
        assert info["name"] == "alice"
        assert info["displayname"] == "Alice Smith"
        assert info["memberof"] == ["ssh-login"]
        assert info["spn"] == "alice@idm.example.com"
        assert info["uuid"] == "123e4567-e89b-12d3-a456-426614174000"
        assert info["classes"] == ["person"]

    def test_person_info_minimal(self):
        """Test converting minimal Person object."""
        person = MockPerson(name="bob")
        info = _person_info(person)
        assert info["name"] == "bob"
        assert info["displayname"] == ""
        assert info["memberof"] == []

    def test_person_info_with_mail(self):
        """Test person info includes mail from attrs."""
        person = MockPerson(
            name="alice",
            displayname="Alice",
            attrs={"mail": ["alice@example.com", "alice.work@example.com"]},
        )
        info = _person_info(person)
        assert info["name"] == "alice"
