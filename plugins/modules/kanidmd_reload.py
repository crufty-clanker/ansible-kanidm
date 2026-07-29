#!/usr/bin/python
# kanidmd_reload.py - Reload Kanidm server configuration using the kanidmd binary.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidmd_reload
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Reload Kanidm server configuration
    description:
      - Reloads the Kanidm server configuration without restarting the service.
      - Uses the kanidmd scripting reload command.
      - The server must be running for this command to succeed.
    options:
      state:
        description: Desired state of the reload operation.
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
- name: Reload Kanidm configuration
  kanidm_community.kanidm.kanidmd_reload:
    state: present
"""

RETURN = r"""
reloaded:
  description: Whether the reload was successful.
  type: bool
  returned: always
"""

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

    class KanidmdReloadModule(KanidmdModuleMixin, AnsibleModule):
        pass

    module = KanidmdReloadModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, reloaded=False, msg="Check mode: reload would be performed.")

    # Check if kanidmd is available
    if not module._ensure_kanidmd_available():
        module.fail_json(msg="kanidmd binary not found or not executable.")

    if state == "absent":
        module.exit_json(changed=False, reloaded=False, msg="Reload not needed (state=absent).")

    # state == "present" - perform the reload
    cmd = ["scripting", "reload"]
    rc, stdout, stderr = module._run_kanidmd(cmd)

    if rc != 0:
        module.fail_json(
            msg=f"Reload failed: {stderr}",
            reloaded=False,
            rc=rc,
        )

    module.exit_json(
        changed=True,
        reloaded=True,
        msg="Kanidm configuration reloaded successfully.",
    )


if __name__ == "__main__":
    main()
