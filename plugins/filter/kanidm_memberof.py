#!/usr/bin/python
# kanidm_memberof.py - Filter plugin to get groups a user belongs to in Kanidm.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    name: kanidm_memberof
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Get groups a Kanidm user belongs to
    description:
      - Queries a Kanidm server and returns the list of groups a user is a member of.
    options:
      _terms:
        description: Username to query.
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
- name: Get groups for a user
  set_fact:
    user_groups: "{{ 'alice' | kanidm_memberof(server='https://idm.example.com', session_token=kanidm_session_token) }}"

- name: Use user groups
  debug:
    msg: "Alice is in groups: {{ user_groups }}"

- name: Check if user is in a specific group
  fail:
    msg: "User does not have ssh-login access"
  when: "'ssh-login' not in ('alice' | kanidm_memberof(server='https://idm.example.com', session_token=kanidm_session_token))"
"""

RETURN = r"""
_raw:
  description: List of group names the user belongs to.
  type: list
  elements: str
  returned: always
  sample: ["ssh-login", "docker-users", "developers"]
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


def kanidm_memberof(username, server, session_token=None, username_auth=None,
                   password=None, password_env=None, kanidm_verify_tls=True,
                   kanidm_ca_path=None):
    """Get groups a Kanidm user belongs to.

    Args:
        username: Username to query.
        server: Kanidm server URL.
        session_token: Existing session token (optional).
        username_auth: Username for authentication (if no token).
        password: Password for authentication (if no token).
        password_env: Environment variable containing password (if no direct password).
        kanidm_verify_tls: Verify TLS certificates.
        kanidm_ca_path: Path to CA certificate for self-signed servers.

    Returns:
        List of group names.
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
        auth_username = username_auth or username
        if not auth_username or not password:
            if password_env:
                import os
                password = os.environ.get(password_env)
            if not auth_username or not password:
                raise AnsibleFilterError("Either 'session_token' or both 'username_auth' and 'password' (or 'password_env') must be provided.")

        init_resp = _run_async(client.auth_init(auth_username))
        session_id = init_resp.response.headers.get("x-kanidm-auth-session-id", "")
        _run_async(client.auth_begin(method="password", sessionid=session_id))
        auth_state = _run_async(client.auth_step_password(password=password, sessionid=session_id))
        token = auth_state.state.success
        if not token:
            raise AnsibleFilterError("Authentication did not return a session token.")
        config.auth_token = token
        client = kanidm.KanidmClient(config=config)

    try:
        person = _run_async(client.person_account_get(username))
        return person.memberof
    except NoMatchingEntries:
        raise AnsibleFilterError(f"User '{username}' not found in Kanidm.")
    except Exception as e:
        raise AnsibleFilterError(f"Failed to get groups for user '{username}': {e}")


class FilterModule(object):
    """Kanidm filter plugins."""

    def filters(self):
        return {
            "kanidm_memberof": kanidm_memberof,
        }
