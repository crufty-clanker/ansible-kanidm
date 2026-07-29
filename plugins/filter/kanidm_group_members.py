#!/usr/bin/python
# kanidm_group_members.py - Filter plugin to get group members from Kanidm.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    name: kanidm_group_members
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Get members of a Kanidm group
    description:
      - Queries a Kanidm server and returns the list of members for a given group.
    options:
      _terms:
        description: Group name(s) to query.
        required: true
        type: str
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
      kanidm_verify_tls:
        description: Verify TLS certificates.
        type: bool
        default: true
      kanidm_ca_path:
        description: Path to a CA certificate PEM file for self-signed servers.
        type: str
    requirements:
      - kanidm (Python library)
"""

EXAMPLES = r"""
- name: Get members of ssh-login group
  set_fact:
    ssh_members: "{{ 'ssh-login' | kanidm_group_members(server='https://idm.example.com', session_token=kanidm_session_token) }}"

- name: Use group members
  debug:
    msg: "SSH members: {{ ssh_members }}"

- name: Get multiple groups
  set_fact:
    group_members: >-
      {{ ['ssh-login', 'docker-users'] | map('kanidm_group_members', server='https://idm.example.com', session_token=kanidm_session_token) | list }}
"""

RETURN = r"""
_raw:
  description: List of group member usernames.
  type: list
  elements: str
  returned: always
  sample: ["alice", "bob", "charlie"]
"""

from ansible.errors import AnsibleFilterError
from ansible.module_utils.common.text.converters import to_text

try:
    import kanidm  # type: ignore[import-untyped]
    from kanidm.exceptions import NoMatchingEntries  # type: ignore[import-untyped]
    HAS_KANIDM = True
except ImportError:
    HAS_KANIDM = False


def _run_async(coro):
    """Run an async coroutine synchronously."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def kanidm_group_members(group_name, server, session_token=None, username=None,
                        password=None, password_env=None, kanidm_verify_tls=True,
                        kanidm_ca_path=None):
    """Get members of a Kanidm group.

    Args:
        group_name: Name of the group to query.
        server: Kanidm server URL.
        session_token: Existing session token (optional).
        username: Username for authentication (if no token).
        password: Password for authentication (if no token).
        password_env: Environment variable containing password (if no direct password).
        kanidm_verify_tls: Verify TLS certificates.
        kanidm_ca_path: Path to CA certificate for self-signed servers.

    Returns:
        List of member usernames.
    """
    if not HAS_KANIDM:
        raise AnsibleFilterError("The 'kanidm' Python library is required for this filter.")

    from kanidm.types import KanidmClientConfig

    config = KanidmClientConfig(
        uri=server,
        verify_certificate=kanidm_verify_tls,
        ca_path=kanidm_ca_path,
    )
    if session_token:
        config.auth_token = session_token

    client = kanidm.KanidmClient(config=config)

    if session_token:
        valid = _run_async(client.check_token_valid(session_token))
        if not valid:
            raise AnsibleFilterError("Session token is invalid or expired.")
    else:
        if not username or not password:
            if password_env:
                import os
                password = os.environ.get(password_env)
            if not username or not password:
                raise AnsibleFilterError("Either 'session_token' or both 'username' and 'password' (or 'password_env') must be provided.")

        init_resp = _run_async(client.auth_init(username))
        session_id = init_resp.response.headers.get("x-kanidm-auth-session-id", "")
        _run_async(client.auth_begin(method="password", sessionid=session_id))
        auth_state = _run_async(client.auth_step_password(password=password, sessionid=session_id))
        token = auth_state.state.success
        if not token:
            raise AnsibleFilterError("Authentication did not return a session token.")
        config.auth_token = token
        client = kanidm.KanidmClient(config=config)

    try:
        group = _run_async(client.group_get(group_name))
        return group.member
    except NoMatchingEntries:
        raise AnsibleFilterError(f"Group '{group_name}' not found in Kanidm.")
    except Exception as e:
        raise AnsibleFilterError(f"Failed to get members of group '{group_name}': {e}")


class FilterModule(object):
    """Kanidm filter plugins."""

    def filters(self):
        return {
            "kanidm_group_members": kanidm_group_members,
        }
