#!/usr/bin/python
# kanidmd.py - Shared module utilities for kanidmd binary operations.
#
# Provides utilities for running kanidmd commands idempotently on the server.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

_KANIDMD_BINARY = "kanidmd"

_LOGGER = logging.getLogger("ansible.module_utils.kanidmd")


def kanidmd_argument_spec():
    """Return the common argument spec shared by all kanidmd modules."""
    return dict(
        kanidmd_binary=dict(
            type="str",
            default=_KANIDMD_BINARY,
            description=f"Path to the kanidmd binary (default: {_KANIDMD_BINARY}).",
        ),
        kanidmd_config_path=dict(
            type="str",
            description="Path to kanidmd configuration file.",
        ),
        kanidmd_db_path=dict(
            type="str",
            description="Path to the Kanidm database directory.",
        ),
        kanidmd_domain=dict(
            type="str",
            description="Kanidm domain name (overrides config file).",
        ),
        kanidmd_run_as_user=dict(
            type="str",
            description="User to run kanidmd as (default: current user).",
            default="",
        ),
    )


class KanidmdModuleMixin:
    """Mixin for modules that use the kanidmd binary directly.

    All kanidmd commands run locally on the server and require appropriate
    privileges (typically the 'kanidm' service user).
    """

    def __init__(self, *args, **kwargs):
        self._kanidmd_binary = kwargs.pop("kanidmd_binary", _KANIDMD_BINARY)
        self._kanidmd_config_path = kwargs.pop("kanidmd_config_path", None)
        self._kanidmd_db_path = kwargs.pop("kanidmd_db_path", None)
        self._kanidmd_domain = kwargs.pop("kanidmd_domain", None)
        self._kanidmd_run_as_user = kwargs.pop("kanidmd_run_as_user", "")
        super().__init__(*args, **kwargs)

    def _build_kanidmd_args(self, subcommand: List[str]) -> List[str]:
        """Build the full kanidmd command arguments."""
        args = [self._kanidmd_binary]

        if self._kanidmd_config_path:
            args.extend(["-c", self._kanidmd_config_path])

        if self._kanidmd_db_path:
            args.extend(["--db-path", self._kanidmd_db_path])

        if self._kanidmd_domain:
            args.extend(["--domain", self._kanidmd_domain])

        args.extend(subcommand)
        return args

    def _run_kanidmd(self, subcommand: List[str], check_mode: bool = False) -> Tuple[int, str, str]:
        """Run a kanidmd command and return (rc, stdout, stderr).

        Args:
            subcommand: List of subcommand arguments (e.g., ['database', 'backup', '/path/to/backup']).
            check_mode: If True, only check what would be done without executing.

        Returns:
            Tuple of (return_code, stdout, stderr).

        Raises:
            SystemExit: If kanidmd binary not found or command fails.
        """
        args = self._build_kanidmd_args(subcommand)

        if check_mode:
            _LOGGER.info("Check mode: would run: %s", " ".join(args))
            return 0, "", ""

        _LOGGER.info("Running: %s", " ".join(args))
        rc, stdout, stderr = self.run_command(args, check_rc=False)

        if rc != 0:
            _LOGGER.error("kanidmd command failed: rc=%d, stderr=%s", rc, stderr)

        return rc, stdout, stderr

    def _parse_json_output(self, stdout: str) -> Optional[Dict[str, Any]]:
        """Parse JSON output from kanidmd, if any.

        kanidmd outputs JSON for some commands (e.g., domain show).
        Most maintenance commands output plain text.
        """
        if not stdout.strip():
            return None
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return None

    def _ensure_kanidmd_available(self) -> bool:
        """Check if kanidmd binary is available."""
        rc, stdout, stderr = self.run_command([self._kanidmd_binary, "version"], check_rc=False)
        return rc == 0
