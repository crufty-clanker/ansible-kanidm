# Ansible Kanidm Modules

This directory contains Ansible modules for managing Kanidm identity management platform.

## HTTP API Modules (pykanidm)

These modules use the [pykanidm](https://pypi.org/project/pykanidm/) Python library to communicate with the Kanidm HTTP API.

| Module | Description |
|--------|-------------|
| [kanidm_auth](kanidm_auth.py) | Authenticate against a Kanidm server |
| [kanidm_group](kanidm_group.py) | Manage Kanidm groups |
| [kanidm_person](kanidm_person.py) | Manage Kanidm person accounts |
| [kanidm_service_account](kanidm_service_account.py) | Manage Kanidm service accounts |
| [kanidm_ssh_key](kanidm_ssh_key.py) | Manage SSH keys on Kanidm accounts |
| [kanidm_api_token](kanidm_api_token.py) | Manage service account API tokens |
| [kanidm_denied_names](kanidm_denied_names.py) | Manage denied names list |
| [kanidm_password_badlist](kanidm_password_badlist.py) | Manage password badlist |

## Binary Modules (kanidmd)

These modules use the `kanidmd` binary directly for server-side operations.

| Module | Description |
|--------|-------------|
| [kanidmd_backup](kanidmd_backup.py) | Create database backups |
| [kanidmd_restore](kanidmd_restore.py) | Restore database from backup |
| [kanidmd_reload](kanidmd_reload.py) | Reload server configuration |
| [kanidmd_verify](kanidmd_verify.py) | Verify database consistency |
| [kanidmd_domain](kanidmd_domain.py) | Manage domain settings |
| [kanidmd_healthcheck](kanidmd_healthcheck.py) | Run server health checks |
| [kanidmd_disable_account](kanidmd_disable_account.py) | Disable an account |
| [kanidmd_recover_account](kanidmd_recover_account.py) | Recover (re-enable) an account |
| [kanidmd_vacuum](kanidmd_vacuum.py) | Vacuum database to reclaim space |
| [kanidmd_reindex](kanidmd_reindex.py) | Reindex database |
| [kanidmd_configtest](kanidmd_configtest.py) | Test server configuration |

## Common Options

All modules accept these common options:

| Option | Description |
|--------|-------------|
| `kanidmd_binary` | Path to the kanidmd binary (default: `kanidmd`) |
| `kanidmd_config_path` | Path to kanidmd configuration file |
| `kanidmd_db_path` | Path to the Kanidm database directory |

HTTP API modules also accept:

| Option | Description |
|--------|-------------|
| `server` | Kanidm server URL (e.g., `https://idm.example.com`) |
| `session_token` | Existing session token (no_log) |
| `username` | Username for authentication |
| `password` | Password for authentication (no_log) |
| `password_env` | Environment variable containing password |
| `kanidm_verify_tls` | Verify TLS certificates (default: `true`) |
| `kanidm_ca_path` | Path to CA certificate for self-signed servers |

## Examples

### HTTP API Module

```yaml
- name: Create a group
  kanidm_community.kanidm.kanidm_group:
    server: "https://idm.example.com"
    username: "admin"
    password_env: "KANIDM_ADMIN_PASSWORD"
    name: "ssh-login"
    state: present
```

### Binary Module

```yaml
- name: Backup database
  kanidm_community.kanidm.kanidmd_backup:
    path: "/var/lib/kanidm/backups/pre-upgrade-{{ ansible_date_time.iso8601_basic_short }}"
    state: present
  become: true
```

## Requirements

- Python 3.11+
- `kanidm` Python package (for HTTP API modules)
- `kanidmd` binary (for binary modules)

## License

MIT
