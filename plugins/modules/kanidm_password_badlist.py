#!/usr/bin/python
# kanidm_password_badlist.py - Manage Kanidm password badlist.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidm_password_badlist
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Manage Kanidm password badlist
    description:
      - Manages the list of passwords that cannot be used for Kanidm accounts.
      - Passwords in this list will be rejected during password changes.
    options:
      server:
        description: Kanidm server URL (e.g. C(https://idm.example.com)).
        type: str
        required: true
      session_token:
        description: Existing Kanidm session token. Omit to authenticate with username/password.
        type: str
        no_log: true
      username:
        description: Username for Kanidm authentication.
        type: str
      password:
        description: Password for Kanidm authentication.
        type: str
        no_log: true
      password_env:
        description: Name of an environment variable containing the password.
        type: str
      passwords:
        description: List of passwords to add to the badlist.
        type: list
        elements: str
        required: true
      state:
        description: Desired state of the password badlist.
        type: str
        choices: ["present", "absent"]
        default: "present"
      kanidm_verify_tls:
        description: Verify TLS certificates.
        type: bool
        default: true
      kanidm_ca_path:
        description: Path to a CA certificate PEM file for self-signed servers.
        type: str
"""

EXAMPLES = r"""
- name: Add common passwords to badlist
  kanidm_community.kanidm.kanidm_password_badlist:
    server: "https://idm.example.com"
    username: "admin"
    password_env: "KANIDM_ADMIN_PASSWORD"
    passwords:
      - "password"
      - "123456"
      - "qwerty"
    state: present

- name: Remove passwords from badlist
  kanidm_community.kanidm.kanidm_password_badlist:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    passwords:
      - "old-password"
    state: absent
"""

RETURN = r"""
passwords:
  description: The current list of badlisted passwords.
  type: list
  elements: str
  returned: on success
  no_log: true
changed_passwords:
  description: Passwords that were added or removed.
  type: list
  elements: str
  returned: on success
  no_log: true
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kanidm_community.kanidm.plugins.module_utils.kanidm import (
    KanidmModuleMixin,
    _run_async,
    kanidm_argument_spec,
)


def main():
    """Entry point."""
    argument_spec = kanidm_argument_spec()
    argument_spec.update(
        dict(
            passwords=dict(type="list", elements="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        )
    )

    class KanidmPasswordBadlistModule(KanidmModuleMixin, AnsibleModule):
        pass

    module = KanidmPasswordBadlistModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    passwords = module.params["passwords"]
    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode: password badlist operation would be performed.")

    # Authenticate
    try:
        module._authenticate()
    except SystemExit:
        raise
    except Exception as exc:
        module.fail_json(msg=f"Authentication failed: {exc}")

    client = module.kanidm_client

    try:
        if state == "present":
            # Get current badlist
            current_passwords = _run_async(client.system_password_badlist_get())
            if not current_passwords:
                current_passwords = []

            # Calculate changes
            passwords_to_add = [p for p in passwords if p not in current_passwords]
            if passwords_to_add:
                _run_async(client.system_password_badlist_append(passwords_to_add))

            module.exit_json(
                changed=bool(passwords_to_add),
                passwords=current_passwords + passwords_to_add,
                changed_passwords=passwords_to_add,
                msg=f"Added {len(passwords_to_add)} password(s) to badlist.",
            )
        else:
            # Get current badlist
            current_passwords = _run_async(client.system_password_badlist_get())
            if not current_passwords:
                current_passwords = []

            # Calculate changes
            passwords_to_remove = [p for p in passwords if p in current_passwords]
            if passwords_to_remove:
                _run_async(client.system_password_badlist_remove(passwords_to_remove))

            remaining = [p for p in current_passwords if p not in passwords_to_remove]
            module.exit_json(
                changed=bool(passwords_to_remove),
                passwords=remaining,
                changed_passwords=passwords_to_remove,
                msg=f"Removed {len(passwords_to_remove)} password(s) from badlist.",
            )
    except Exception as exc:
        module.fail_json(msg=f"Failed to manage password badlist: {exc}")


if __name__ == "__main__":
    main()
