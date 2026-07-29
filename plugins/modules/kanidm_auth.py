#!/usr/bin/python
# kanidm_auth.py - Authenticate against a Kanidm server and obtain a session token.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidm_auth
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Authenticate against a Kanidm server
    description:
      - Performs the Kanidm 3-step authentication flow (init, begin, cred)
        against the server's HTTP API and returns a session token.
      - The returned session token can be passed as C(session_token) to
        other kanidm_community.kanidm modules to skip re-authentication.
      - The token is stored in the module result under C(session_token) and
        can be passed to other Kanidm modules via C(session_token).
    options:
      server:
        description: Kanidm server URL (e.g. C(https://idm.example.com)).
        type: str
        required: true
      username:
        description: Username to authenticate as.
        type: str
        required: true
      password:
        description: Password for authentication.
        type: str
        no_log: true
      password_env:
        description: Name of an environment variable containing the password.
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
- name: Authenticate and capture token
  kanidm_community.kanidm.kanidm_auth:
    server: "https://idm.example.com"
    username: "admin"
    password_env: "KANIDM_ADMIN_PASSWORD"
  register: auth_result

- name: Save token for later use
  ansible.builtin.set_fact:
    kanidm_session_token: "{{ auth_result.session_token }}"

- name: Create a group using the token
  kanidm_community.kanidm.kanidm_group:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    name: "ssh-login"
    state: present
"""

RETURN = r"""
session_token:
  description: The Kanidm session token (JWS) obtained from authentication.
  type: str
  returned: always
  no_log: true
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kanidm_community.kanidm.plugins.module_utils.kanidm import (  # noqa: E402
    KanidmModuleMixin,
    kanidm_argument_spec,
)


def main():
    """Entry point."""
    argument_spec = kanidm_argument_spec()
    argument_spec.update(
        dict(
            username=dict(type="str", required=True),
        )
    )

    class KanidmAuthModule(KanidmModuleMixin, AnsibleModule):
        pass

    if module.check_mode:
        module.exit_json(changed=False)

    try:
        token = module._authenticate()
    except SystemExit:
        raise
    except Exception as exc:
        module.fail_json(msg=f"Authentication failed: {exc}")

    result = dict(
        changed=False,
        session_token=token,
    )
    module.exit_json(**result)


if __name__ == "__main__":
    main()
