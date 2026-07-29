#!/usr/bin/python
# kanidmd_healthcheck.py - Run health checks on a running Kanidm server.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidmd_healthcheck
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Run health checks on a running Kanidm server
    description:
      - Uses the kanidmd scripting healthcheck command to verify that
        the Kanidm server is running and all services are listening.
      - Can be used with ansible.builtin.wait_for or ansible.builtin.uri
        to poll until the server is ready.
    options:
      verify_tls:
        description: Disable TLS verification for the health check.
        type: bool
        default: false
      check_origin:
        description: Check the 'origin' URL instead of 'address'.
        type: bool
        default: false
      kanidmd_binary:
        description: Path to the kanidmd binary.
        type: str
        default: kanidmd
      kanidmd_config_path:
        description: Path to kanidmd configuration file.
        type: str
"""

EXAMPLES = r"""
- name: Wait for Kanidm to be ready
  kanidm_community.kanidm.kanidmd_healthcheck:
    verify_tls: true
  register: healthcheck

- name: Display health check result
  debug:
    msg: "Kanidm health check: {{ healthcheck.status }}"

- name: Use as a wait_for condition
  ansible.builtin.wait_for:
    timeout: 60
    exec: "kanidmd scripting healthcheck"
"""

RETURN = r"""
status:
  description: Health check status (ok, warning, error).
  type: str
  returned: always
services:
  description: List of services checked.
  type: list
  elements: dict
  returned: on success
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kanidm_community.kanidm.plugins.module_utils.kanidmd import (
    KanidmdModuleMixin,
    kanidmd_argument_spec,
)


def main():
    """Entry point."""
    argument_spec = kanidmd_argument_spec()
    argument_spec.update(
        dict(
            verify_tls=dict(type="bool", default=False),
            check_origin=dict(type="bool", default=False),
        )
    )

    class KanidmdHealthcheckModule(KanidmdModuleMixin, AnsibleModule):
        pass

    module = KanidmdHealthcheckModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    verify_tls = module.params.get("verify_tls", False)
    check_origin = module.params.get("check_origin", False)

    if module.check_mode:
        module.exit_json(changed=False, status="ok", msg="Check mode: healthcheck would run.")

    # Build the healthcheck command
    cmd = ["scripting", "healthcheck"]
    if verify_tls:
        cmd.append("--verify-tls")
    if check_origin:
        cmd.append("--check-origin")

    rc, stdout, stderr = module._run_kanidmd(cmd)

    if rc != 0:
        # Parse error output if possible
        error_info = module._parse_json_output(stderr) or {"raw": stderr.strip()}
        module.fail_json(
            msg=f"Health check failed: {stderr}",
            status="error",
            error=error_info,
            rc=rc,
        )

    # Parse success output
    health_info = module._parse_json_output(stdout)
    if not health_info:
        health_info = {"status": "ok", "raw": stdout.strip()}

    status = health_info.get("status", "ok")

    module.exit_json(
        changed=False,
        status=status,
        services=health_info.get("services", []),
        msg=f"Health check completed with status: {status}.",
    )


if __name__ == "__main__":
    main()
