#!/usr/bin/python
# kanidmd_configtest.py - Test Kanidm configuration using the kanidmd binary.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
    module: kanidmd_configtest
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Test Kanidm server configuration
    description:
      - Tests the Kanidm server configuration without starting network listeners.
      - Uses the kanidmd configtest command.
      - Useful for validating configuration changes before restarting the server.
    options:
      state:
        description: Desired state of the configtest operation.
        type: str
        choices: ["present", "absent"]
        default: "present"
      kanidmd_binary:
        description: Path to the kanidmd binary.
        type: str
        default: kanidmd
      kanidmd_config_path:
        description: Path to kanidmd configuration file.
        type: str
"""

EXAMPLES = r"""
- name: Test configuration before restart
  kanidm_community.kanidm.kanidmd_configtest:
    state: present
  register: configtest_result

- name: Display config test results
  debug:
    msg: "Configuration test: {{ configtest_result.status }}"
"""

RETURN = r"""
status:
  description: Configuration test status (ok, warning, error).
  type: str
  returned: always
warnings:
  description: List of warnings found during configuration test.
  type: list
  elements: str
  returned: on success
validated:
  description: Whether the configuration is valid.
  type: bool
  returned: always
"""

import json


def main():
    """Entry point."""
    argument_spec = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        kanidmd_binary=dict(type="str", default="kanidmd"),
        kanidmd_config_path=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, validated=False, msg="Check mode: configtest would be performed.")

    # Build the command
    cmd = [module.params["kanidmd_binary"], "configtest"]
    if module.params.get("kanidmd_config_path"):
        cmd.extend(["-c", module.params["kanidmd_config_path"]])

    if state == "absent":
        module.exit_json(changed=False, validated=False, msg="Configtest not needed (state=absent).")

    # Run the command
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc != 0:
        # Parse error output if possible
        error_info = {}
        if stderr.strip():
            try:
                error_info = json.loads(stderr) if stderr.strip().startswith("{") else {"raw": stderr.strip()}
            except json.JSONDecodeError:
                error_info = {"raw": stderr.strip()}

        module.fail_json(
            msg=f"Configuration test failed: {stderr}",
            status="error",
            validated=False,
            error=error_info,
            rc=rc,
        )

    # Parse success output
    config_info = {}
    if stdout.strip():
        try:
            config_info = json.loads(stdout) if stdout.strip().startswith("{") else {"raw": stdout.strip()}
        except json.JSONDecodeError:
            config_info = {"raw": stdout.strip()}

    status = config_info.get("status", "ok")
    warnings = config_info.get("warnings", [])

    module.exit_json(
        changed=False,
        status=status,
        warnings=warnings,
        validated=status == "ok",
        msg=f"Configuration test completed with status: {status}.",
    )


if __name__ == "__main__":
    main()
