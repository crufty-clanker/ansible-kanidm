# kanidm_community.kanidm.kanidm Role

Install and configure Kanidm identity server with optional certbot-managed TLS certificates.

## Requirements

- Ansible >= 2.15
- Linux system with systemd
- `curl`, `ca-certificates`, `libsqlite3-dev` packages
- Internet access to download Kanidm binary (or pre-staged binary)
- Port 8443 (or configured) exposed for Kanidm
- Port 80 (or configured) exposed for certbot HTTP-01 challenge

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `kanidm_version` | `"1.3.3"` | Kanidm version to install |
| `kanidm_arch` | `{{ ansible_architecture }}` | Target architecture |
| `kanidm_install_dir` | `"/usr/local/bin"` | Installation directory |
| `kanidm_service_user` | `"kanidm"` | Service system user |
| `kanidm_service_group` | `"kanidm"` | Service system group |
| `kanidm_listen_address` | `"0.0.0.0:8443"` | Address and port to bind |
| `kanidm_domain` | `"idm.example.com"` | Server domain name |
| `kanidm_data_dir` | `"/var/lib/kanidm"` | Data directory |
| `kanidm_log_level` | `"info"` | Log level (trace/debug/info/warn/error) |
| `kanidm_admin_email` | `"admin@example.com"` | Admin email address |
| `kanidm_certbot_enabled` | `false` | Enable certbot-managed TLS |
| `kanidm_certbot_email` | `"admin@example.com"` | Certbot account email |
| `kanidm_certbot_ca_server` | `"https://acme-v02.api.letsencrypt.org/directory"` | ACME CA server URL |
| `kanidm_certificate_dir` | `"/etc/kanidm/certs"` | TLS certificate directory |
| `kanidm_tls_cert_file` | `""` | Path to TLS cert (manual mode) |
| `kanidm_tls_key_file` | `""` | Path to TLS key (manual mode) |
| `kanidm_http_port` | `80` | HTTP port for certbot challenge |
| `kanidm_database_path` | `"/var/lib/kanidm/kanidm.db"` | Database file path |
| `kanidm_service_name` | `"kanidm"` | Systemd service name |
| `kanidm_service_state` | `"started"` | Desired service state |
| `kanidm_service_enabled` | `true` | Enable on boot |

## Example Playbook

```yaml
- name: Install Kanidm
  hosts: kanidm_servers
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm
      kanidm_domain: "idm.example.com"
      kanidm_admin_email: "admin@example.com"
      kanidm_certbot_enabled: true
      kanidm_certbot_email: "admin@example.com"
```

## Manual TLS Certificates

When `kanidm_certbot_enabled: false`, provide paths to existing certificates:

```yaml
kanidm_certbot_enabled: false
kanidm_tls_cert_file: "/etc/ssl/certs/kanidm.pem"
kanidm_tls_key_file: "/etc/ssl/private/kanidm.key"
```

## Upgrades

Kanidm requires **sequential upgrades** — you must upgrade through each version in sequence (e.g. 1.5 → 1.6 → 1.7). Skip upgrades are not supported.

The role handles this automatically: if the target version is more than one minor version ahead, it will block with instructions on which intermediate version to install first.

### Upgrade workflow

1. Role checks if the current binary exists (fresh install vs upgrade)
2. On fresh install: skips upgrade check (no data to protect), downloads binary, starts service
3. On upgrade: runs `kanidmd domain upgrade-check` **before** downloading anything
4. If check fails: stops immediately — no download, no service change
5. If check passes: downloads new binary and restarts service

### Example

**Fresh install** — just set the version:

```yaml
- hosts: kanidm_servers
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm
      kanidm_version: "1.5.0"
```

**Upgrade** — go through each minor version:

```yaml
# Step 1: Upgrade to 1.4.0
kanidm_version: "1.4.0"
# Step 2: After confirming 1.4.0 works, upgrade to 1.5.0
kanidm_version: "1.5.0"
```

If the upgrade check reports failures, resolve them manually and re-run the role.

## Idempotency

This role is idempotent. Running it multiple times will not produce changes on subsequent runs.

**Note:** Service restart is skipped when the binary version is unchanged, preventing unnecessary downtime on repeated runs.

## License

MIT

## Author Information

Kanidm Community Collection
