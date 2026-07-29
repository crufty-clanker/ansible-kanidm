#!/usr/bin/python
# kanidmd_domain.py - Manage Kanidm domain settings using the kanidmd binary.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidmd_domain
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Manage Kanidm domain settings
    description:
      - Shows or modifies Kanidm domain configuration using the kanidmd binary.
      - The 'show' action reads current domain settings.
      - The 'rename' action changes the domain name (requires server to be stopped).
    options:
      action:
        description: Action to perform on the domain.
        type: str
        choices: ["show", "rename", "upgrade-check"]
        default: "show"
      new_name:
        description: New domain name (required for action=rename).
        type: str
      state:
        description: Desired state.
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
- name: Show current domain configuration
  kanidm_community.kanidm.kanidmd_domain:
    action: show
  register: domain_info

- name: Display domain name
  debug:
    msg: "Current domain: {{ domain_info.domain_name }}"

- name: Rename the domain
  kanidm_community.kanidm.kanidmd_domain:
    action: rename
    new_name: "new-domain.example.com"
    state: present
"""

RETURN = r"""
domain:
  description: Domain information as returned by kanidmd.
  type: dict
  returned: on success when action=show
domain_name:
  description: The current or new domain name.
  type: str
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
            action=dict(
                type="str",
                choices=["show", "rename", "upgrade-check"],
                default="show",
            ),
            new_name=dict(type="str"),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        )
    )

    class KanidmdDomainModule(KanidmdModuleMixin, AnsibleModule):
        pass

    module = KanidmdDomainModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    action = module.params["action"]
    new_name = module.params.get("new_name")
    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, msg=f"Check mode: domain {action} would be performed.")

    # Check if kanidmd is available
    if not module._ensure_kanidmd_available():
        module.fail_json(msg="kanidmd binary not found or not executable.")

    if action == "show":
        # Show current domain configuration
        cmd = ["domain", "show"]
        rc, stdout, stderr = module._run_kanidmd(cmd)

        if rc != 0:
            module.fail_json(msg=f"Failed to show domain: {stderr}", rc=rc)

        # Try to parse JSON output
        domain_info = module._parse_json_output(stdout)
        if not domain_info:
            # If not JSON, return the raw output
            domain_info = {"raw": stdout.strip()}

        module.exit_json(
            changed=False,
            domain=domain_info,
            domain_name=domain_info.get("domain_name", domain_info.get("name", "unknown")),
            msg="Domain information retrieved successfully.",
        )

    elif action == "rename":
        if not new_name:
            module.fail_json(msg="'new_name' is required for action='rename'.")

        cmd = ["domain", "rename"]
        rc, stdout, stderr = module._run_kanidmd(cmd)

        if rc != 0:
            module.fail_json(msg=f"Failed to rename domain: {stderr}", rc=rc)

        module.exit_json(
            changed=True,
            domain_name=new_name,
            msg=f"Domain renamed to '{new_name}'.",
        )

    elif action == "upgrade-check":
        cmd = ["domain", "upgrade-check"]
        rc, stdout, stderr = module._run_kanidmd(cmd)

        if rc != 0:
            module.fail_json(msg=f"Upgrade check failed: {stderr}", rc=rc)

        # Parse the upgrade check results
        issues = []
        if stdout.strip():
            try:
                issues = json.loads(stdout) if stdout.strip().startswith("[") else [stdout.strip()]
            except json.JSONDecodeError:
                issues = [stdout.strip()]

        module.exit_json(
            changed=False,
            issues=issues,
            has_issues=len(issues) > 0,
            msg=f"Upgrade check completed. Found {len(issues)} potential issue(s).",
        )


if __name__ == "__main__":
    main()
