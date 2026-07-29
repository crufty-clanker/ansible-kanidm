#!/usr/bin/python
# kanidm_group.py - Manage Kanidm groups via the HTTP API.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidm_group
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Manage Kanidm groups
    description:
      - Create, update, or delete groups and manage their member lists
        via the Kanidm HTTP API (using pykanidm).
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
      name:
        description: Name of the group. Required when C(state=present) or C(state=absent).
        type: str
      state:
        description: Desired state of the group.
        type: str
        choices: ["present", "absent"]
        default: "present"
      members:
        description: List of group member names. Replaces the current member list when C(state=present).
        type: list
        elements: str
        default: []
      kanidm_verify_tls:
        description: Verify TLS certificates.
        type: bool
        default: true
      kanidm_ca_path:
        description: Path to a CA certificate PEM file for self-signed servers.
        type: str
"""

EXAMPLES = r"""
- name: Create a group
  kanidm_community.kanidm.kanidm_group:
    server: "https://idm.example.com"
    username: "admin"
    password_env: "KANIDM_ADMIN_PASSWORD"
    name: "ssh-login"
    state: present

- name: Add members to a group
  kanidm_community.kanidm.kanidm_group:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    name: "ssh-login"
    members:
      - alice
      - bob
    state: present

- name: Remove a group
  kanidm_community.kanidm.kanidm_group:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    name: "old-team"
    state: absent
"""

RETURN = r"""
group:
  description: The group object as returned by the Kanidm API.
  type: dict
  returned: on success
  sample: {"name": "ssh-login", "member": ["alice"], "spn": "ssh-login@idm.example.com", ...}
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kanidm_community.kanidm.plugins.module_utils.kanidm import (
    KanidmModuleMixin,
    _run_async,
    kanidm_argument_spec,
)


def _members_need_update(current_members, desired_members):
    """Check if member lists differ (ignoring order)."""
    return set(current_members) != set(desired_members)


def main():
    """Entry point."""
    argument_spec = kanidm_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            members=dict(type="list", elements="str", default=[]),
        )
    )

    class KanidmGroupModule(KanidmModuleMixin, AnsibleModule):
        pass

    module = KanidmGroupModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params["name"]
    state = module.params["state"]
    members = module.params.get("members", [])

    if module.check_mode:
        module.exit_json(changed=False)

    # Authenticate
    try:
        module._authenticate()
    except SystemExit:
        raise
    except Exception as exc:
        module.fail_json(msg=f"Authentication failed: {exc}")

    client = module.kanidm_client

    if state == "absent":
        # Delete the group
        try:
            result = _run_async(client.group_delete(name))
            if result.status_code in (200, 204):
                module.exit_json(changed=True, msg=f"Group '{name}' deleted.")
            module.fail_json(msg=f"Failed to delete group '{name}': HTTP {result.status_code}")
        except Exception as exc:
            module.fail_json(msg=f"Failed to delete group '{name}': {exc}")

    # state == "present"
    # Check if group exists
    try:
        group = _run_async(client.group_get(name))
    except Exception:
        group = None

    changed = False
    group_info = {}

    if group is None:
        # Create the group
        try:
            result = _run_async(client.group_create(name))
            if result.status_code in (200, 201):
                changed = True
                module.exit_json(changed=True, msg=f"Group '{name}' created.")
            module.fail_json(msg=f"Failed to create group '{name}': HTTP {result.status_code}")
        except Exception as exc:
            module.fail_json(msg=f"Failed to create group '{name}': {exc}")
    else:
        # Group exists — update members if needed
        group_info = {
            "name": group.name,
            "member": group.member,
            "dynmember": group.dynmember,
            "spn": group.spn,
            "uuid": group.uuid,
            "gidnumber": group.gidnumber,
        }

        if members and _members_need_update(group.member, members):
            try:
                result = _run_async(client.group_set_members(group.uuid, members))
                if result.status_code in (200, 204):
                    changed = True
                    group_info["member"] = members
                else:
                    module.fail_json(msg=f"Failed to set members on group '{name}': HTTP {result.status_code}")
            except Exception as exc:
                module.fail_json(msg=f"Failed to set members on group '{name}': {exc}")

    module.exit_json(changed=changed, group=group_info)


if __name__ == "__main__":
    main()
