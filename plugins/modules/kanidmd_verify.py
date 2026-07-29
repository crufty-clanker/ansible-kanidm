#!/usr/bin/python
# kanidmd_verify.py - Verify Kanidm database consistency using the kanidmd binary.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidmd_verify
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Verify Kanidm database consistency
    description:
      - Verifies the Kanidm database and entity consistency using the kanidmd binary.
      - Uses the kanidmd database verify command.
      - This is a read-only operation that can be performed while the server is running.
    options:
      state:
        description: Desired state of the verify operation.
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
      kanidmd_db_path:
        description: Path to the Kanidm database directory.
        type: str
"""

EXAMPLES = r"""
- name: Verify database consistency
  kanidm_community.kanidm.kanidmd_verify:
    state: present
  register: verify_result

- name: Display verification results
  debug:
    msg: "Database verification: {{ verify_result.status }}"
"""

RETURN = r"""
status:
  description: Verification status (ok, warning, error).
  type: str
  returned: always
issues:
  description: List of issues found during verification.
  type: list
  elements: str
  returned: on success
verified:
  description: Whether the verification was successful.
  type: bool
  returned: always
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
            state=dict(type="str", choices=["present", "absent"], default="present"),
        )
    )

    class KanidmdVerifyModule(KanidmdModuleMixin, AnsibleModule):
        pass

    module = KanidmdVerifyModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, verified=False, msg="Check mode: verify would be performed.")

    # Check if kanidmd is available
    if not module._ensure_kanidmd_available():
        module.fail_json(msg="kanidmd binary not found or not executable.")

    if state == "absent":
        module.exit_json(changed=False, verified=False, msg="Verify not needed (state=absent).")

    # state == "present" - perform the verify
    cmd = ["database", "verify"]
    rc, stdout, stderr = module._run_kanidmd(cmd)

    if rc != 0:
        module.fail_json(
            msg=f"Verification failed: {stderr}",
            status="error",
            verified=False,
            rc=rc,
        )

    # Parse the output
    verify_info = module._parse_json_output(stdout)
    if not verify_info:
        # If not JSON, assume success if rc was 0
        verify_info = {"status": "ok"}

    status = verify_info.get("status", "ok")
    issues = verify_info.get("issues", [])

    module.exit_json(
        changed=False,
        status=status,
        issues=issues,
        verified=status == "ok",
        msg=f"Database verification completed with status: {status}.",
    )


if __name__ == "__main__":
    main()
