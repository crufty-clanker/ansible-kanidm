#!/usr/bin/python
# kanidmd_vacuum.py - Vacuum Kanidm database using the kanidmd binary.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
    module: kanidmd_vacuum
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Vacuum Kanidm database to reclaim space
    description:
      - Vacuums the Kanidm database to reclaim space or change database
        filesystem type/page size.
      - Uses the kanidmd database vacuum command.
      - The server must be stopped before running vacuum.
    options:
      state:
        description: Desired state of the vacuum operation.
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
- name: Vacuum database to reclaim space
  kanidm_community.kanidm.kanidmd_vacuum:
    state: present
  become: true
"""

RETURN = r"""
vacuumed:
  description: Whether the vacuum was successful.
  type: bool
  returned: always
"""


def main():
    """Entry point."""
    argument_spec = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        kanidmd_binary=dict(type="str", default="kanidmd"),
        kanidmd_config_path=dict(type="str"),
        kanidmd_db_path=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, vacuumed=False, msg="Check mode: vacuum would be performed.")

    # Build the command
    cmd = [module.params["kanidmd_binary"], "database", "vacuum"]
    if module.params.get("kanidmd_config_path"):
        cmd.extend(["-c", module.params["kanidmd_config_path"]])
    if module.params.get("kanidmd_db_path"):
        cmd.extend(["--db-path", module.params["kanidmd_db_path"]])

    if state == "absent":
        module.exit_json(changed=False, vacuumed=False, msg="Vacuum not needed (state=absent).")

    # Run the command
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc != 0:
        module.fail_json(
            msg=f"Failed to vacuum database: {stderr}",
            vacuumed=False,
            rc=rc,
        )

    module.exit_json(
        changed=True,
        vacuumed=True,
        msg="Database vacuumed successfully.",
    )


if __name__ == "__main__":
    main()
