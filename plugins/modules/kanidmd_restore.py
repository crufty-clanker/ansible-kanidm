#!/usr/bin/python
# kanidmd_restore.py - Restore Kanidm database from backup using the kanidmd binary.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidmd_restore
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Restore Kanidm database from backup
    description:
      - Restores the Kanidm database from a backup created by kanidmd_backup.
      - The server must be stopped before running a restore.
      - This is a destructive operation that replaces the current database.
    options:
      path:
        description: Path to the backup file to restore from.
        type: str
        required: true
      state:
        description: Desired state of the restore operation.
        type: str
        choices: ["present", "absent"]
        default: "present"
      kanidmd_binary:
        description: Path to the kanidmd binary.
        type: str
        default: kanidmd
      kanidmd_config_path:
        description: Path to kanidmd configuration file.
        type: str
      kanidmd_db_path:
        description: Path to the Kanidm database directory.
        type: str
"""

EXAMPLES = r"""
- name: Restore database from backup
  kanidm_community.kanidm.kanidmd_restore:
    path: "/var/lib/kanidm/backups/pre-upgrade-20240101T000000"
    state: present
  become: true
"""

RETURN = r"""
path:
  description: Path to the backup file that was restored.
  type: str
  returned: on success
restored:
  description: Whether the restore was successful.
  type: bool
  returned: always
"""

import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kanidm_community.kanidm.plugins.module_utils.kanidmd import (
    KanidmdModuleMixin,
    kanidmd_argument_spec,
)


def main():
    """Entry point."""
    argument_spec = kanidmd_argument_spec()
    argument_spec.update(
        dict(
            path=dict(type="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        )
    )

    class KanidmdRestoreModule(KanidmdModuleMixin, AnsibleModule):
        pass

    module = KanidmdRestoreModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    path = module.params["path"]
    state = module.params["state"]

    if module.check_mode:
        module.exit_json(changed=False, path=path, msg="Check mode: restore would be performed.")

    # Check if kanidmd is available
    if not module._ensure_kanidmd_available():
        module.fail_json(msg="kanidmd binary not found or not executable.")

    # Check if backup file exists
    if not os.path.exists(path):
        module.fail_json(msg=f"Backup file not found: '{path}'", path=path, restored=False)

    if state == "absent":
        # Nothing to do for absent state
        module.exit_json(changed=False, path=path, restored=False, msg="Restore not needed (state=absent).")

    # state == "present" - perform the restore
    cmd = ["database", "restore", path]
    rc, stdout, stderr = module._run_kanidmd(cmd)

    if rc != 0:
        module.fail_json(
            msg=f"Restore failed: {stderr}",
            path=path,
            restored=False,
            rc=rc,
        )

    module.exit_json(
        changed=True,
        path=path,
        restored=True,
        msg=f"Database restored successfully from '{path}'.",
    )


if __name__ == "__main__":
    main()
