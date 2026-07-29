#!/usr/bin/python
# kanidm_ssh_key.py - Manage SSH public keys on Kanidm persons and service accounts.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidm_ssh_key
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Manage SSH public keys on Kanidm accounts
    description:
      - Add or remove SSH public keys on Kanidm person or service account
        identities via the Kanidm HTTP API (using pykanidm).
      - Each key is identified by a C(tag) (e.g. "laptop", "workstation") so
        multiple keys can coexist on a single account.
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
      principal:
        description: Name of the person or service account to manage keys for.
        type: str
        required: true
      principal_type:
        description: Whether the principal is a person or service account.
        type: str
        choices: ["person", "service_account"]
        default: "person"
      tag:
        description: Tag/label for the SSH key (e.g. "laptop", "workstation"). Used as the key identifier.
        type: str
        required: true
      pubkey:
        description: The SSH public key string (e.g. "ssh-ed25519 AAAA... user@host").
        type: str
      state:
        description: Desired state of the SSH key.
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
- name: Add an SSH key to a person
  kanidm_community.kanidm.kanidm_ssh_key:
    server: "https://idm.example.com"
    username: "admin"
    password_env: "KANIDM_ADMIN_PASSWORD"
    principal: "alice"
    principal_type: "person"
    tag: "laptop"
    pubkey: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... alice@laptop"
    state: present

- name: Add an SSH key to a service account
  kanidm_community.kanidm.kanidm_ssh_key:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    principal: "backup-agent"
    principal_type: "service_account"
    tag: "backup-server"
    pubkey: "ssh-rsa AAAAB3NzaC1yc2EAAA... backup@backup"
    state: present

- name: Remove an SSH key
  kanidm_community.kanidm.kanidm_ssh_key:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    principal: "alice"
    principal_type: "person"
    tag: "old-laptop"
    state: absent
"""

RETURN = r"""
key:
  description: Information about the SSH key operation performed.
  type: dict
  returned: on success
  sample: {"principal": "alice", "principal_type": "person", "tag": "laptop", "state": "present"}
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
            principal=dict(type="str", required=True),
            principal_type=dict(
                type="str", choices=["person", "service_account"], default="person"
            ),
            tag=dict(type="str", required=True),
            pubkey=dict(type="str"),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        )
    )

    class KanidmSshKeyModule(KanidmModuleMixin, AnsibleModule):
        pass

    module = KanidmSshKeyModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    principal = module.params["principal"]
    principal_type = module.params["principal_type"]
    tag = module.params["tag"]
    pubkey = module.params.get("pubkey")
    state = module.params["state"]

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
        # Remove the SSH key
        try:
            if principal_type == "person":
                result = _run_async(client.person_account_delete_ssh_key(principal, tag))
            else:
                result = _run_async(client.service_account_delete_ssh_pubkey(principal, tag))

            if result.status_code in (200, 204):
                module.exit_json(
                    changed=True,
                    key={
                        "principal": principal,
                        "principal_type": principal_type,
                        "tag": tag,
                        "state": "absent",
                    },
                )
            module.fail_json(
                msg=f"Failed to remove SSH key '{tag}' from {principal_type} '{principal}': HTTP {result.status_code}"
            )
        except Exception as exc:
            module.fail_json(msg=f"Failed to remove SSH key '{tag}': {exc}")

    # state == "present" — add the SSH key
    if not pubkey:
        module.fail_json(msg="'pubkey' is required when state=present.")

    try:
        if principal_type == "person":
            result = _run_async(client.person_account_post_ssh_key(principal, tag, pubkey))
        else:
            result = _run_async(client.service_account_post_ssh_pubkey(principal, tag, pubkey))

        if result.status_code in (200, 201):
            module.exit_json(
                changed=True,
                key={
                    "principal": principal,
                    "principal_type": principal_type,
                    "tag": tag,
                    "state": "present",
                },
            )
        module.fail_json(
            msg=f"Failed to add SSH key '{tag}' to {principal_type} '{principal}': HTTP {result.status_code}"
        )
    except Exception as exc:
        module.fail_json(msg=f"Failed to add SSH key '{tag}': {exc}")


if __name__ == "__main__":
    main()
