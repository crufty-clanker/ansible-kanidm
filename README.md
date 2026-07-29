# Ansible Collection - kanidm_community.kanidm

This collection provides Ansible roles for deploying and managing [Kanidm](https://kanidm.com/), a modern identity management platform.

## Roles

| Role | Description |
|------|-------------|
| `kanidm_server` | Install and configure Kanidm server |
| `kanidm_client` | Install Kanidm client CLI tools |
| `kanidm_unixd` | Install and configure kanidm_unixd for PAM/SSSD integration |

## Requirements

- Ansible >= 2.15
- Target systems: Debian 12+ or Ubuntu 22.04+

## Installation

```bash
ansible-galaxy collection install kanidm_community.kanidm
```

## Documentation

- [Upgrade Guide](docs/docsite/rst/upgrades.rst) — Sequential upgrade process

## Usage

### Install Kanidm Server

```yaml
- name: Install Kanidm Server
  hosts: kanidm_servers
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm_server
      kanidm_domain: "idm.example.com"
      kanidm_admin_email: "admin@example.com"
```

### Install Client Tools

```yaml
- name: Install Kanidm Client
  hosts: all
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm_client
```

### Configure Unix Integration

```yaml
- name: Configure Kanidm Unixd
  hosts: kanidm_clients
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm_unixd
      kanidm_unixd_domain: "idm.example.com"
      kanidm_unixd_server: "https://idm.example.com"
```

## License

MIT

## Author Information

Kanidm Community Collection
