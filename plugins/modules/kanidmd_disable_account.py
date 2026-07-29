#!/usr/bin/python
# kanidmd_disable_account.py - Disable a Kanidm account using the kanidmd binary.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
    module: kanidmd_disable_account
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Disable a Kanidm account
    description:
      - Disables a Kanidm account so that it can no longer be used for authentication.
      - Uses the kanidmd disable-account command.
      - The account can be re-enabled using kanidmd_recover_account.
      - This is an offline operation that may require the server to be stopped.
    options:
      account:
        description: Name of the account to disable.
        type: str
        required: true
      state:
        description: Desired state of the account.
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
- name: Disable a compromised account
  kanidm_community.kanidm.kanidmd_disable_account:
    account: "compromised-user"
    state: present
  become: true
"""

RETURN = r"""
account:
  description: Name of the disabled account.
  type: str
  returned: always
disabled:
  description: Whether the account was successfully disabled.
  type: bool
  returned: always
"""


def main():
    """Entry point."""
    argument_spec = dict(
        account=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        kanidmd_binary=dict(type="str", default="kanidmd"),
        kanidmd_config_path=dict(type="str"),
        kanidmd_db_path=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    account = module.params["account"]
    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, account=account, disabled=False, msg="Check mode: account disable would be performed.")

    # Build the command
    cmd = [module.params["kanidmd_binary"], "disable-account", account]
    if module.params.get("kanidmd_config_path"):
        cmd.extend(["-c", module.params["kanidmd_config_path"]])
    if module.params.get("kanidmd_db_path"):
        cmd.extend(["--db-path", module.params["kanidmd_db_path"]])

    if state == "absent":
        module.exit_json(changed=False, account=account, disabled=False, msg="Account disable not needed (state=absent).")

    # Run the command
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc != 0:
        module.fail_json(
            msg=f"Failed to disable account '{account}': {stderr}",
            account=account,
            disabled=False,
            rc=rc,
        )

    module.exit_json(
        changed=True,
        account=account,
        disabled=True,
        msg=f"Account '{account}' disabled successfully.",
    )


if __name__ == "__main__":
    main()
