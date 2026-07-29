#!/usr/bin/python
# kanidm_service_account.py - Manage Kanidm service accounts via the HTTP API.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidm_service_account
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Manage Kanidm service accounts
    description:
      - Create, or delete service (machine) accounts via the Kanidm HTTP API
        (using pykanidm).
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
        description: Name of the service account. Required.
        type: str
        required: true
      state:
        description: Desired state of the service account.
        type: str
        choices: ["present", "absent"]
        default: "present"
      displayname:
        description: Display name for the service account (e.g. "Backup Agent").
        type: str
      kanidm_verify_tls:
        description: Verify TLS certificates.
        type: bool
        default: true
      kanidm_ca_path:
        description: Path to a CA certificate PEM file for self-signed servers.
        type: str
"""

EXAMPLES = r"""
- name: Create a service account
  kanidm_community.kanidm.kanidm_service_account:
    server: "https://idm.example.com"
    username: "admin"
    password_env: "KANIDM_ADMIN_PASSWORD"
    name: "backup-agent"
    displayname: "Backup Agent"
    state: present

- name: Delete a service account
  kanidm_community.kanidm.kanidm_service_account:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    name: "old-service"
    state: absent
"""

RETURN = r"""
service_account:
  description: The service account as returned by the Kanidm API.
  type: dict
  returned: on success
  sample: {"name": "backup-agent", "displayname": "Backup Agent", "memberof": [], "spn": "backup-agent@idm.example.com", ...}
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kanidm_community.kanidm.plugins.module_utils.kanidm import (
    KanidmModuleMixin,
    _run_async,
    kanidm_argument_spec,
)


def _service_account_info(sa) -> dict:
    """Convert a pykanidm ServiceAccount object to a serializable dict."""
    return {
        "name": sa.name,
        "displayname": sa.displayname,
        "memberof": sa.memberof,
        "spn": sa.spn,
        "uuid": str(sa.uuid),
        "classes": sa.classes,
    }


def main():
    """Entry point."""
    argument_spec = kanidm_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            displayname=dict(type="str"),
        )
    )

    class KanidmServiceAccountModule(KanidmModuleMixin, AnsibleModule):
        pass

    module = KanidmServiceAccountModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params["name"]
    state = module.params["state"]
    displayname = module.params.get("displayname", name)

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
        # Check if service account exists
        try:
            _run_async(client.service_account_get(name))
        except Exception:
            module.exit_json(changed=False, msg=f"Service account '{name}' does not exist.")

        try:
            result = _run_async(client.service_account_delete(name))
            if result.status_code in (200, 204):
                module.exit_json(changed=True, msg=f"Service account '{name}' deleted.")
            module.fail_json(msg=f"Failed to delete service account '{name}': HTTP {result.status_code}")
        except Exception as exc:
            module.fail_json(msg=f"Failed to delete service account '{name}': {exc}")

    # state == "present"
    try:
        sa = _run_async(client.service_account_get(name))
        sa_info = _service_account_info(sa)
        changed = False
    except Exception:
        sa = None
        sa_info = {}
        changed = True

    if sa is None:
        try:
            result = _run_async(client.service_account_create(name, displayname))
            if result.status_code in (200, 201):
                changed = True
                sa = _run_async(client.service_account_get(name))
                sa_info = _service_account_info(sa)
            else:
                module.fail_json(msg=f"Failed to create service account '{name}': HTTP {result.status_code}")
        except Exception as exc:
            module.fail_json(msg=f"Failed to create service account '{name}': {exc}")

    module.exit_json(changed=changed, service_account=sa_info)


if __name__ == "__main__":
    main()
