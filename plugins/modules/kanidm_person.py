#!/usr/bin/python
# kanidm_person.py - Manage Kanidm person accounts via the HTTP API.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidm_person
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Manage Kanidm person accounts
    description:
      - Create, update, or delete person (human user) accounts via the
        Kanidm HTTP API (using pykanidm).
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
        description: Username (RDN) of the person account. Required.
        type: str
        required: true
      state:
        description: Desired state of the person account.
        type: str
        choices: ["present", "absent"]
        default: "present"
      displayname:
        description: Display name for the person (e.g. "Alice Smith").
        type: str
      mail:
        description: Email address(es) for the person. Supports multiple addresses via list.
        type: list
        elements: str
      legalname:
        description: Legal/full name for the person.
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
- name: Create a person
  kanidm_community.kanidm.kanidm_person:
    server: "https://idm.example.com"
    username: "admin"
    password_env: "KANIDM_ADMIN_PASSWORD"
    name: "alice"
    displayname: "Alice Smith"
    mail:
      - alice@example.com
    state: present

- name: Update a person's email
  kanidm_community.kanidm.kanidm_person:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    name: "alice"
    mail:
      - alice.new@example.com
    state: present

- name: Delete a person
  kanidm_community.kanidm.kanidm_person:
    server: "https://idm.example.com"
    session_token: "{{ kanidm_session_token }}"
    name: "alice"
    state: absent
"""

RETURN = r"""
person:
  description: The person account as returned by the Kanidm API.
  type: dict
  returned: on success
  sample: {"name": "alice", "displayname": "Alice Smith", "memberof": ["ssh-login"], "spn": "alice@idm.example.com", ...}
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kanidm_community.kanidm.plugins.module_utils.kanidm import (
    KanidmModuleMixin,
    _run_async,
    kanidm_argument_spec,
)


def _person_info(person) -> dict:
    """Convert a pykanidm Person object to a serializable dict."""
    return {
        "name": person.name,
        "displayname": person.displayname,
        "memberof": person.memberof,
        "spn": person.spn,
        "uuid": str(person.uuid),
        "classes": person.classes,
    }


def main():
    """Entry point."""
    argument_spec = kanidm_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            displayname=dict(type="str"),
            mail=dict(type="list", elements="str"),
            legalname=dict(type="str"),
        )
    )

    class KanidmPersonModule(KanidmModuleMixin, AnsibleModule):
        pass

    module = KanidmPersonModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params["name"]
    state = module.params["state"]
    displayname = module.params.get("displayname")
    mail = module.params.get("mail")
    legalname = module.params.get("legalname")

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
        # Check if person exists
        try:
            _run_async(client.person_account_get(name))
        except Exception:
            module.exit_json(changed=False, msg=f"Person '{name}' does not exist.")

        try:
            result = _run_async(client.person_account_delete(name))
            if result.status_code in (200, 204):
                module.exit_json(changed=True, msg=f"Person '{name}' deleted.")
            module.fail_json(msg=f"Failed to delete person '{name}': HTTP {result.status_code}")
        except Exception as exc:
            module.fail_json(msg=f"Failed to delete person '{name}': {exc}")

    # state == "present"
    # Check if person exists
    try:
        person = _run_async(client.person_account_get(name))
        person_info = _person_info(person)
        changed = False
    except Exception:
        person = None
        person_info = {}
        changed = True

    if person is None:
        # Create the person
        try:
            result = _run_async(client.person_account_create(name, displayname or name))
            if result.status_code in (200, 201):
                person = _run_async(client.person_account_get(name))
                person_info = _person_info(person)
                changed = True
            else:
                module.fail_json(msg=f"Failed to create person '{name}': HTTP {result.status_code}")
        except Exception as exc:
            module.fail_json(msg=f"Failed to create person '{name}': {exc}")
    else:
        # Update if attributes differ
        attrs_to_update = {}
        if displayname and displayname != person.displayname:
            attrs_to_update["displayname"] = displayname
        if mail and mail != person.attrs.get("mail", []):
            attrs_to_update["mail"] = mail
        if legalname and legalname != person.attrs.get("legalname", [legalname])[0]:
            attrs_to_update["legalname"] = legalname

        if attrs_to_update:
            try:
                result = _run_async(
                    client.person_account_update(
                        id=person.uuid,
                        displayname=attrs_to_update.get("displayname"),
                        mail=attrs_to_update.get("mail"),
                        legalname=attrs_to_update.get("legalname"),
                    )
                )
                if result.status_code in (200, 204):
                    changed = True
                    person = _run_async(client.person_account_get(name))
                    person_info = _person_info(person)
                else:
                    module.fail_json(msg=f"Failed to update person '{name}': HTTP {result.status_code}")
            except Exception as exc:
                module.fail_json(msg=f"Failed to update person '{name}': {exc}")

    module.exit_json(changed=changed, person=person_info)


if __name__ == "__main__":
    main()
