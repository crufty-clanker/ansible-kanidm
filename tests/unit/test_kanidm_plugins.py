#!/usr/bin/env python3
# Unit tests for kanidm lookup and filter plugins

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestLookupPlugin:
    """Test kanidm_info lookup plugin structure."""

    def test_lookup_module_exists(self):
        """Test that the lookup module can be imported."""
        try:
            from lookup.kanidm_info import LookupModule
            assert LookupModule is not None
        except ImportError:
            pytest.skip("kanidm library not installed")

    def test_lookup_documentation(self):
        """Test that the lookup has proper documentation."""
        try:
            from lookup.kanidm_info import DOCUMENTATION
            assert "name: kanidm_info" in DOCUMENTATION
            assert "server" in DOCUMENTATION
            assert "query_type" in DOCUMENTATION
        except ImportError:
            pytest.skip("kanidm library not installed")

    def test_lookup_return(self):
        """Test that the lookup has return documentation."""
        try:
            from lookup.kanidm_info import RETURN
            assert "_raw" in RETURN
            assert "dict" in RETURN
        except ImportError:
            pytest.skip("kanidm library not installed")


class TestFilterPlugins:
    """Test kanidm filter plugins structure."""

    def test_group_members_filter_exists(self):
        """Test that the group_members filter can be imported."""
        try:
            from filter.kanidm_group_members import FilterModule, kanidm_group_members
            assert FilterModule is not None
            assert callable(kanidm_group_members)
        except ImportError:
            pytest.skip("kanidm library not installed")

    def test_memberof_filter_exists(self):
        """Test that the memberof filter can be imported."""
        try:
            from filter.kanidm_memberof import FilterModule, kanidm_memberof
            assert FilterModule is not None
            assert callable(kanidm_memberof)
        except ImportError:
            pytest.skip("kanidm library not installed")

    def test_group_members_documentation(self):
        """Test that the group_members filter has proper documentation."""
        try:
            from filter.kanidm_group_members import DOCUMENTATION
            assert "name: kanidm_group_members" in DOCUMENTATION
            assert "server" in DOCUMENTATION
        except ImportError:
            pytest.skip("kanidm library not installed")

    def test_memberof_documentation(self):
        """Test that the memberof filter has proper documentation."""
        try:
            from filter.kanidm_memberof import DOCUMENTATION
            assert "name: kanidm_memberof" in DOCUMENTATION
            assert "server" in DOCUMENTATION
        except ImportError:
            pytest.skip("kanidm library not installed")

    def test_filter_module_returns_filters(self):
        """Test that filter modules return the correct filter dict."""
        try:
            from filter.kanidm_group_members import FilterModule as GMFilter
            from filter.kanidm_memberof import FilterModule as MoFModule

            gm = GMFilter()
            filters = gm.filters()
            assert "kanidm_group_members" in filters

            mf = MoFModule()
            filters = mf.filters()
            assert "kanidm_memberof" in filters
        except ImportError:
            pytest.skip("kanidm library not installed")
