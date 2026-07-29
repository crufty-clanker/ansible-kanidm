#!/usr/bin/python
# kanidmd_recover_account.py - Recover a Kanidm account using the kanidmd binary.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
    module: kanidmd_recover_account
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Recover (re-enable) a Kanidm account
    description:
      - Recovers (re-enables) a previously disabled Kanidm account.
      - Uses the kanidmd scripting recover-account command.
      - The account must have been previously disabled using kanidmd_disable_account.
    options:
      account:
        description: Name of the account to recover.
        type: str
        required: true
      new_password:
        description: New password for the recovered account.
        type: str
        no_log: true
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
"""

EXAMPLES = r"""
- name: Recover a disabled account with new password
  kanidm_community.kanidm.kanidmd_recover_account:
    account: "compromised-user"
    new_password: "{{ lookup('ansible.builtin.password', '/dev/null length=20 chars=ascii_letters,digits') }}"
    state: present
  become: true
"""

RETURN = r"""
account:
  description: Name of the recovered account.
  type: str
  returned: always
recovered:
  description: Whether the account was successfully recovered.
  type: bool
  returned: always
"""


def main():
    """Entry point."""
    argument_spec = dict(
        account=dict(type="str", required=True),
        new_password=dict(type="str", no_log=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        kanidmd_binary=dict(type="str", default="kanidmd"),
        kanidmd_config_path=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    account = module.params["account"]
    new_password = module.params.get("new_password")
    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, account=account, recovered=False, msg="Check mode: account recovery would be performed.")

    # Build the command
    cmd = [module.params["kanidmd_binary"], "scripting", "recover-account", account]
    if module.params.get("kanidmd_config_path"):
        cmd.extend(["-c", module.params["kanidmd_config_path"]])

    if state == "absent":
        module.exit_json(changed=False, account=account, recovered=False, msg="Account recovery not needed (state=absent).")

    # Run the command
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc != 0:
        module.fail_json(
            msg=f"Failed to recover account '{account}': {stderr}",
            account=account,
            recovered=False,
            rc=rc,
        )

    module.exit_json(
        changed=True,
        account=account,
        recovered=True,
        msg=f"Account '{account}' recovered successfully.",
    )


if __name__ == "__main__":
    main()
