#!/usr/bin/python
# kanidmd_backup.py - Create Kanidm database backups using the kanidmd binary.
#
# Copyright: (c) 2024, Kanidm Community Contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
    module: kanidmd_backup
    author: Kanidm Community Contributors
    version_added: "0.2.0"
    short_description: Create Kanidm database backups
    description:
      - Creates offline backups of the Kanidm database using the kanidmd binary.
      - The server must be stopped before running an offline backup.
      - Supports compression via the -C/--compression flag.
    options:
      path:
        description: Output path for the backup file. Must be writable by the kanidm user.
        type: str
        required: true
      compression:
        description: Compression method for the backup (e.g., gzip, zstd).
        type: str
      state:
        description: Desired state of the backup.
        type: str
        choices: ["present", "absent"]
        default: "present"
      remove_old_backups:
        description: Number of old backups to keep (0 = keep all).
        type: int
        default: 0
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
      kanidmd_run_as_user:
        description: User to run kanidmd as (default: current user).
        type: str
        default: ""
"""

EXAMPLES = r"""
- name: Create a backup before upgrade
  kanidm_community.kanidm.kanidmd_backup:
    path: "/var/lib/kanidm/backups/pre-upgrade-{{ ansible_date_time.iso8601_basic_short }}"
    compression: gzip
    state: present

- name: Keep only last 5 backups
  kanidm_community.kanidm.kanidmd_backup:
    path: "/var/lib/kanidm/backups/daily-{{ ansible_date_time.date }}"
    remove_old_backups: 5
    state: present
"""

RETURN = r"""
path:
  description: Path where the backup was created.
  type: str
  returned: on success
backup_size:
  description: Size of the backup file in bytes.
  type: int
  returned: on success
"""

import os
import shutil

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kanidm_community.kanidm.plugins.module_utils.kanidmd import (
    KanidmdModuleMixin,
    kanidmd_argument_spec,
)


def _get_backup_size(path):
    """Get the size of a backup file."""
    if os.path.exists(path):
        return os.path.getsize(path)
    return 0


def main():
    """Entry point."""
    argument_spec = kanidmd_argument_spec()
    argument_spec.update(
        dict(
            path=dict(type="str", required=True),
            compression=dict(type="str"),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            remove_old_backups=dict(type="int", default=0),
        )
    )

    class KanidmdBackupModule(KanidmdModuleMixin, AnsibleModule):
        pass

    module = KanidmdBackupModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    path = module.params["path"]
    compression = module.params.get("compression")
    state = module.params["state"]
    remove_old_backups = module.params.get("remove_old_backups", 0)

    if module.check_mode:
        module.exit_json(changed=False, path=path, msg="Check mode: backup would be created.")

    # Check if kanidmd is available
    if not module._ensure_kanidmd_available():
        module.fail_json(msg="kanidmd binary not found or not executable.")

    if state == "absent":
        # Remove the backup file
        if os.path.exists(path):
            os.remove(path)
            module.exit_json(changed=True, path=path, msg=f"Backup '{path}' removed.")
        else:
            module.exit_json(changed=False, path=path, msg=f"Backup '{path}' does not exist.")

    # state == "present" - create the backup
    if os.path.exists(path):
        module.exit_json(changed=False, path=path, msg=f"Backup already exists at '{path}'.")

    # Build the backup command
    cmd = ["database", "backup"]
    if compression:
        cmd.extend(["-C", compression])
    cmd.append(path)

    # Run the backup
    rc, stdout, stderr = module._run_kanidmd(cmd)

    if rc != 0:
        module.fail_json(msg=f"Backup failed: {stderr}", rc=rc)

    # Verify backup was created
    if not os.path.exists(path):
        module.fail_json(msg=f"Backup command succeeded but file not found at '{path}'.")

    backup_size = _get_backup_size(path)

    # Remove old backups if specified
    if remove_old_backups > 0:
        backup_dir = os.path.dirname(path)
        backup_prefix = os.path.basename(path)
        if os.path.isdir(backup_dir):
            backups = [
                f for f in os.listdir(backup_dir)
                if f.startswith(backup_prefix) and os.path.isfile(os.path.join(backup_dir, f))
            ]
            if len(backups) > remove_old_backups:
                backups.sort()
                to_remove = backups[:len(backups) - remove_old_backups]
                for old_backup in to_remove:
                    old_path = os.path.join(backup_dir, old_backup)
                    os.remove(old_path)

    module.exit_json(
        changed=True,
        path=path,
        backup_size=backup_size,
        msg=f"Backup created successfully at '{path}' ({backup_size} bytes).",
    )


if __name__ == "__main__":
    main()
