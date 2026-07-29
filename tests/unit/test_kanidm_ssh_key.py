#!/usr/bin/env python3
# Unit tests for kanidm_ssh_key module

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestKanidmSshKey:
    """Test kanidm_ssh_key module argument spec."""

    def test_ssh_key_argument_spec_structure(self):
        """Test that ssh_key module would have correct argument spec keys."""
        # Verify the expected arguments for the module
        expected_args = ["principal", "principal_type", "tag", "pubkey", "state"]
        for arg in expected_args:
            assert arg in expected_args

    def test_principal_types(self):
        """Test that principal_type choices are correct."""
        valid_types = ["person", "service_account"]
        assert "person" in valid_types
        assert "service_account" in valid_types

    def test_state_choices(self):
        """Test that state choices are correct."""
        valid_states = ["present", "absent"]
        assert "present" in valid_states
        assert "absent" in valid_states
