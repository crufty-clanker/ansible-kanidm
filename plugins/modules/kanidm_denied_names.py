#!/usr/bin/python
# kanidm_denied_names.py - Manage Kanidm denied names list.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidm_denied_names
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Manage Kanidm denied names list
    description:
      - Manages the list of names that cannot be used for Kanidm accounts.
      - Names in this list will be rejected during account creation.
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
      names:
        description: List of names to add to the denied names list.
        type: list
        elements: str
        required: true
      state:
        description: Desired state of the denied names.
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
- name: Add names to denied list
  kanidm_community.kanidm.kanidm_denied_names:
    server: "https://idm.example.com"
    username: "admin"
    password_env: "KANIDM_ADMIN_PASSWORD"
    names:
      - "admin"
      - "root"
      - "test"
    state: present

- name: Remove names from denied list
  kanidm_community.kanidm.kanidm_denied_names:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    names:
      - "old-name"
    state: absent
"""

RETURN = r"""
names:
  description: The current list of denied names.
  type: list
  elements: str
  returned: on success
changed_names:
  description: Names that were added or removed.
  type: list
  elements: str
  returned: on success
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
            names=dict(type="list", elements="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        )
    )

    class KanidmDeniedNamesModule(KanidmModuleMixin, AnsibleModule):
        pass

    module = KanidmDeniedNamesModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    names = module.params["names"]
    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode: denied names operation would be performed.")

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
            # Get current denied names
            current_names = _run_async(client.system_denied_names_get())
            if not current_names:
                current_names = []

            # Calculate changes
            names_to_add = [n for n in names if n not in current_names]
            if names_to_add:
                _run_async(client.system_denied_names_append(names_to_add))

            module.exit_json(
                changed=bool(names_to_add),
                names=current_names + names_to_add,
                changed_names=names_to_add,
                msg=f"Added {len(names_to_add)} name(s) to denied list.",
            )
        else:
            # Get current denied names
            current_names = _run_async(client.system_denied_names_get())
            if not current_names:
                current_names = []

            # Calculate changes
            names_to_remove = [n for n in names if n in current_names]
            if names_to_remove:
                _run_async(client.system_denied_names_remove(names_to_remove))

            remaining = [n for n in current_names if n not in names_to_remove]
            module.exit_json(
                changed=bool(names_to_remove),
                names=remaining,
                changed_names=names_to_remove,
                msg=f"Removed {len(names_to_remove)} name(s) from denied list.",
            )
    except Exception as exc:
        module.fail_json(msg=f"Failed to manage denied names: {exc}")


if __name__ == "__main__":
    main()
