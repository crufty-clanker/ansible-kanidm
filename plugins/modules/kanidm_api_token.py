#!/usr/bin/python
# kanidm_api_token.py - Manage Kanidm service account API tokens.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidm_api_token
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Manage Kanidm service account API tokens
    description:
      - Creates or destroys API tokens for Kanidm service accounts.
      - API tokens can be used for authentication with the Kanidm HTTP API.
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
      account:
        description: Name of the service account to manage tokens for.
        type: str
        required: true
      token_label:
        description: Label for the API token (used for identification).
        type: str
        required: true
      expiry:
        description: Token expiry in RFC3339 format (e.g., "2024-12-31T23:59:59Z").
        type: str
        required: true
      read_write:
        description: Whether the token has read-write access.
        type: bool
        default: false
      state:
        description: Desired state of the token.
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
- name: Create an API token for backup agent
  kanidm_community.kanidm.kanidm_api_token:
    server: "https://idm.example.com"
    username: "admin"
    password_env: "KANIDM_ADMIN_PASSWORD"
    account: "backup-agent"
    token_label: "backup-token-2024"
    expiry: "2025-01-01T00:00:00Z"
    read_write: false
    state: present

- name: Revoke an API token
  kanidm_community.kanidm.kanidm_api_token:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    account: "backup-agent"
    token_label: "old-token"
    state: absent
"""

RETURN = r"""
token:
  description: API token information (only returned on creation).
  type: dict
  returned: on success when state=present
  no_log: true
token_id:
  description: The token ID (UUID).
  type: str
  returned: on success
"""

import json
from datetime import datetime

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
            account=dict(type="str", required=True),
            token_label=dict(type="str", required=True),
            expiry=dict(type="str", required=True),
            read_write=dict(type="bool", default=False),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        )
    )

    class KanidmApiTokenModule(KanidmModuleMixin, AnsibleModule):
        pass

    module = KanidmApiTokenModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    account = module.params["account"]
    token_label = module.params["token_label"]
    expiry = module.params["expiry"]
    read_write = module.params.get("read_write", False)
    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode: API token operation would be performed.")

    # Validate expiry format
    try:
        datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        module.fail_json(msg=f"Invalid expiry format: '{expiry}'. Expected RFC3339 format (e.g., '2024-12-31T23:59:59Z').")

    # Authenticate
    try:
        module._authenticate()
    except SystemExit:
        raise
    except Exception as exc:
        module.fail_json(msg=f"Authentication failed: {exc}")

    client = module.kanidm_client

    if state == "absent":
        # Delete the API token
        # Note: pykanidm doesn't have a direct method to delete by label,
        # so we'd need to list tokens and find the right one.
        # For now, we'll use a placeholder that would need server-side token listing.
        module.fail_json(
            msg=f"Deleting API tokens by label is not yet supported. Manual intervention required.",
            account=account,
            token_label=token_label,
        )

    # state == "present" - create the API token
    try:
        result = _run_async(
            client.service_account_generate_api_token(
                account_id=account,
                label=token_label,
                expiry=expiry,
                read_write=read_write,
            )
        )

        if result.status_code in (200, 201):
            # Parse the response to extract token info
            token_info = {}
            if result.data:
                if isinstance(result.data, dict):
                    token_info = result.data
                elif isinstance(result.data, str):
                    try:
                        token_info = json.loads(result.data)
                    except json.JSONDecodeError:
                        token_info = {"raw": result.data}

            module.exit_json(
                changed=True,
                token=token_info,
                token_id=token_info.get("id", token_info.get("token_id", "unknown")),
                msg=f"API token '{token_label}' created for account '{account}'.",
            )
        else:
            module.fail_json(
                msg=f"Failed to create API token: HTTP {result.status_code}",
                account=account,
                token_label=token_label,
            )
    except Exception as exc:
        module.fail_json(
            msg=f"Failed to create API token: {exc}",
            account=account,
            token_label=token_label,
        )


if __name__ == "__main__":
    main()
