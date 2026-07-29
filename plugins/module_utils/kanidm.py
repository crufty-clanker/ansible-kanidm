#!/usr/bin/python
# kanidm.py - Shared module utilities for Kanidm Ansible modules
#
# Provides async wrappers around pykanidm (kanidm) so synchronous Ansible
# modules can authenticate and call the Kanidm HTTP API.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

if TYPE_CHECKING:
    from kanidm import KanidmClient  # type: ignore[import-untyped]

_KANIDM_IMPORT_ERROR: Optional[str] = None
try:
    import kanidm  # type: ignore[import-untyped]
except ImportError as exc:
    _KANIDM_IMPORT_ERROR = str(exc)

from kanidm.exceptions import (  # type: ignore[import-untyped]
    AuthBeginFailed,
    AuthCredFailed,
    AuthInitFailed,
    AuthMechUnknown,
    NoMatchingEntries,
)
from kanidm.types import (  # type: ignore[import-untyped]
    KanidmClientConfig,
)

_KANIDM_LIB_REQUIRED = missing_required_lib("kanidm")

_LOGGER = logging.getLogger("ansible.module_utils.kanidm")


def _run_async(coro):
    """Run an async coroutine synchronously.

    Ansible modules run synchronously, but pykanidm is fully async.
    This helper bridges the gap using asyncio.run().
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class KanidmModuleMixin:
    """Mixin that provides Kanidm authentication and client construction.

    Subclass this from AnsibleModule and call ``self._authenticate()``
    before performing any API operations.
    """

    def __init__(self, *args, **kwargs):
        # Pop our extras before AnsibleModule sees them
        self._kanidm_verify_tls = kwargs.pop("kanidm_verify_tls", True)
        self._kanidm_ca_path = kwargs.pop("kanidm_ca_path", None)
        super().__init__(*args, **kwargs)

    @property
    def kanidm_client(self) -> "KanidmClient":
        """Lazy-initialized KanidmClient."""
        if not hasattr(self, "_kanidm_client_cache"):
            if _KANIDM_IMPORT_ERROR is not None:
                self.fail_json(msg=f"Python 'kanidm' library is required but not found. {_KANIDM_IMPORT_ERROR}")
            self._kanidm_client_cache = self._build_client()
        return self._kanidm_client_cache

    def _build_client(self) -> "KanidmClient":
        """Construct a KanidmClient from module params."""
        config = KanidmClientConfig(
            uri=self.params.get("server"),
            verify_certificate=self._kanidm_verify_tls,
            ca_path=self._kanidm_ca_path,
        )
        if self.session_token:
            config.auth_token = self.session_token
        return kanidm.KanidmClient(config=config)

    @property
    def session_token(self) -> Optional[str]:
        return self.params.get("session_token")

    def _authenticate(self) -> str:
        """Perform the 3-step Kanidm auth flow.

        Returns the session token (JWS). If a session_token was already
        provided, validates it with the server instead.
        """
        if _KANIDM_IMPORT_ERROR is not None:
            self.fail_json(msg=f"Python 'kanidm' library is required but not found. {_KANIDM_IMPORT_ERROR}")

        if self.session_token:
            # Validate existing token
            token = self.session_token
            try:
                valid = _run_async(self.kanidm_client.check_token_valid(token))
            except Exception as exc:
                self.fail_json(msg=f"Failed to validate session token: {exc}")
            if not valid:
                self.fail_json(msg="Session token is invalid or expired. Re-authenticate with username/password.")
            return token

        # 3-step auth flow via POST /v1/auth
        username = self.params.get("username")
        password = self._resolve_password()

        if not username or not password:
            self.fail_json(
                msg="Either 'session_token' or both 'username' and 'password' (or 'password_env') must be provided."
            )

        client = self._build_client()  # fresh client without token

        # Step 1: init
        try:
            init_resp = _run_async(client.auth_init(username))
        except AuthInitFailed as exc:
            self.fail_json(msg=f"Kanidm auth init failed: {exc}")
        except Exception as exc:
            self.fail_json(msg=f"Kanidm auth init error: {exc}")

        session_id = init_resp.response.headers.get("x-kanidm-auth-session-id", "")

        # Step 2: begin (password method)
        try:
            begin_resp = _run_async(client.auth_begin(method="password", sessionid=session_id))
        except AuthBeginFailed as exc:
            self.fail_json(msg=f"Kanidm auth begin failed: {exc}")
        except Exception as exc:
            self.fail_json(msg=f"Kanidm auth begin error: {exc}")

        # Step 3: credential step
        try:
            auth_state = _run_async(client.auth_step_password(password=password, sessionid=session_id))
        except AuthCredFailed as exc:
            self.fail_json(msg=f"Kanidm authentication failed (bad credentials): {exc}")
        except AuthMechUnknown as exc:
            self.fail_json(msg=f"Kanidm authentication mechanism unknown: {exc}")
        except Exception as exc:
            self.fail_json(msg=f"Kanidm auth step error: {exc}")

        token = auth_state.state.success
        if not token:
            self.fail_json(msg="Kanidm auth did not return a session token.")

        return token

    def _resolve_password(self) -> Optional[str]:
        """Resolve password from direct param or environment variable."""
        if self.params.get("password"):
            return self.params["password"]
        env_var = self.params.get("password_env")
        if env_var:
            import os
            return os.environ.get(env_var)
        return None

    def _handle_api_error(self, exc, context=""):
        """Convert pykanidm exceptions to Ansible-friendly messages."""
        if isinstance(exc, NoMatchingEntries):
            self.fail_json(msg=f"Kanidm: {context} — entry not found: {exc}")
        elif isinstance(exc, (AuthInitFailed, AuthBeginFailed, AuthCredFailed)):
            self.fail_json(msg=f"Kanidm auth error ({context}): {exc}")
        else:
            self.fail_json(msg=f"Kanidm API error ({context}): {exc}")


def kanidm_argument_spec():
    """Return the common argument spec shared by all Kanidm modules."""
    return dict(
        server=dict(
            type="str",
            required=True,
            description="Kanidm server URL (e.g. https://idm.example.com).",
        ),
        session_token=dict(
            type="str",
            no_log=True,
            description=(
                "Existing Kanidm session token (JWS). "
                "Omit to authenticate with username/password."
            ),
        ),
        username=dict(
            type="str",
            description="Username for Kanidm authentication.",
        ),
        password=dict(
            type="str",
            no_log=True,
            description="Password for Kanidm authentication. Use password_env for secrets.",
        ),
        password_env=dict(
            type="str",
            description=(
                "Name of an environment variable containing the password. "
                "Takes precedence over 'password' if both are empty."
            ),
        ),
        kanidm_verify_tls=dict(
            type="bool",
            default=True,
            description="Verify TLS certificates when connecting to the Kanidm server.",
        ),
        kanidm_ca_path=dict(
            type="str",
            description="Path to a CA certificate PEM file for self-signed servers.",
        ),
    )
