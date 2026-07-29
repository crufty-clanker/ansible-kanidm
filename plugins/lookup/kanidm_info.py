#!/usr/bin/python
# kanidm_info.py - Lookup plugin to query Kanidm for user/group information.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    name: kanidm_info
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Query Kanidm for user, group, or attribute information
    description:
      - Queries a Kanidm server for information about users, groups, or specific attributes.
      - Returns structured data that can be used in playbooks for dynamic configuration.
    options:
      _terms:
        description: Terms to look up.
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
      query_type:
        description: Type of query to perform.
        type: str
        choices: ["user", "group", "attr"]
        default: "user"
      query_name:
        description: Name of the user or group to query.
        type: str
      attribute:
        description: Attribute to retrieve (required when C(query_type=attr)).
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
- name: Look up user info
  set_fact:
    user_info: "{{ lookup('kanidm_info', 'alice', server='https://idm.example.com', username='admin', password_env='KANIDM_ADMIN_PASSWORD') }}"

- name: Use user info in a task
  debug:
    msg: "Alice is in groups: {{ user_info.memberof }}"

- name: Look up group members
  set_fact:
    group_info: "{{ lookup('kanidm_info', 'ssh-login', server='https://idm.example.com', session_token=kanidm_session_token, query_type='group') }}"

- name: Get a specific attribute
  set_fact:
    user_email: "{{ lookup('kanidm_info', 'alice', server='https://idm.example.com', session_token=kanidm_session_token, query_type='attr', attribute='mail') }}"
"""

RETURN = r"""
_raw:
  description: The queried data as a dictionary.
  type: dict
  returned: always
  sample: {"name": "alice", "displayname": "Alice Smith", "memberof": ["ssh-login"], "spn": "alice@idm.example.com"}
"""

from ansible.errors import AnsibleError, AnsibleLookupError
from ansible.plugins.lookup import LookupBase

try:
    import kanidm  # type: ignore[import-untyped]
    from kanidm.exceptions import NoMatchingEntries  # type: ignore[import-untyped]
    HAS_KANIDM = True
except ImportError:
    HAS_KANIDM = False

from ansible.module_utils.common.text.converters import to_text


def _run_async(coro):
    """Run an async coroutine synchronously."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class LookupModule(LookupBase):

    def _authenticate(self, server, username, password, password_env, session_token, verify_tls, ca_path):
        """Authenticate against Kanidm and return a client."""
        if not HAS_KANIDM:
            raise AnsibleError("The 'kanidm' Python library is required for this lookup plugin.")

        from kanidm.types import KanidmClientConfig

        config = KanidmClientConfig(
            uri=server,
            verify_certificate=verify_tls,
            ca_path=ca_path,
        )
        if session_token:
            config.auth_token = session_token

        client = kanidm.KanidmClient(config=config)

        if session_token:
            valid = _run_async(client.check_token_valid(session_token))
            if not valid:
                raise AnsibleLookupError("Session token is invalid or expired.")
        else:
            if not username or not password:
                if password_env:
                    import os
                    password = os.environ.get(password_env)
                if not username or not password:
                    raise AnsibleLookupError("Either 'session_token' or both 'username' and 'password' (or 'password_env') must be provided.")

            # 3-step auth flow
            init_resp = _run_async(client.auth_init(username))
            session_id = init_resp.response.headers.get("x-kanidm-auth-session-id", "")
            _run_async(client.auth_begin(method="password", sessionid=session_id))
            auth_state = _run_async(client.auth_step_password(password=password, sessionid=session_id))
            token = auth_state.state.success
            if not token:
                raise AnsibleLookupError("Authentication did not return a session token.")
            config.auth_token = token
            client = kanidm.KanidmClient(config=config)

        return client

    def run(self, terms, variables=None, **kwargs):
        """Run the lookup."""
        self.set_options(var_options=variables, direct=kwargs)

        server = self.get_option("server")
        session_token = self.get_option("session_token")
        username = self.get_option("username")
        password = self.get_option("password")
        password_env = self.get_option("password_env")
        query_type = self.get_option("query_type")
        query_name = self.get_option("query_name")
        attribute = self.get_option("attribute")
        verify_tls = self.get_option("kanidm_verify_tls")
        ca_path = self.get_option("kanidm_ca_path")

        if len(terms) < 1:
            raise AnsibleLookupError("At least one term is required.")

        term = terms[0]

        try:
            client = self._authenticate(
                server=server,
                username=username,
                password=password,
                password_env=password_env,
                session_token=session_token,
                verify_tls=verify_tls,
                ca_path=ca_path,
            )

            if query_type == "user":
                person = _run_async(client.person_account_get(term))
                result = {
                    "name": person.name,
                    "displayname": person.displayname,
                    "memberof": person.memberof,
                    "spn": person.spn,
                    "uuid": str(person.uuid),
                    "classes": person.classes,
                }
            elif query_type == "group":
                group = _run_async(client.group_get(term))
                result = {
                    "name": group.name,
                    "member": group.member,
                    "dynmember": group.dynmember,
                    "spn": group.spn,
                    "uuid": group.uuid,
                    "gidnumber": group.gidnumber,
                }
            elif query_type == "attr":
                if not attribute:
                    raise AnsibleLookupError("Attribute name is required when query_type='attr'.")
                # Try to get the attribute from person first
                try:
                    person = _run_async(client.person_account_get(term))
                    attr_value = person.attrs.get(attribute, [])
                except Exception:
                    # Try group
                    try:
                        group = _run_async(client.group_get(term))
                        attr_value = group.attrs.get(attribute, [])
                    except Exception:
                        raise AnsibleLookupError(f"Could not find '{term}' as a person or group.")
                result = {
                    "principal": term,
                    "attribute": attribute,
                    "value": attr_value if isinstance(attr_value, list) else [attr_value],
                }
            else:
                raise AnsibleLookupError(f"Unknown query_type: {query_type}")

            return [result]

        except NoMatchingEntries as e:
            raise AnsibleLookupError(f"Kanidm entry not found: {term} - {e}")
        except Exception as e:
            raise AnsibleLookupError(f"Kanidm lookup failed: {e}")
