# Ansible Collection - kanidm_community.kanidm

This collection provides Ansible roles for deploying and managing [Kanidm](https://kanidm.com/), a modern identity management platform.

## Roles

| Role | Description |
|------|-------------|
| `kanidm-server` | Install and configure Kanidm server |
| `kanidm-client` | Install Kanidm client CLI tools |
| `kanidm-unixd` | Install and configure kanidm-unixd for PAM/SSSD integration |

## Requirements

- Ansible >= 2.15
- Target systems: Debian 12+ or Ubuntu 22.04+

## Installation

```bash
ansible-galaxy collection install kanidm_community.kanidm
```

## Usage

### Install Kanidm Server

```yaml
- name: Install Kanidm Server
  hosts: kanidm_servers
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm-server
      kanidm_domain: "idm.example.com"
      kanidm_admin_email: "admin@example.com"
```

### Install Client Tools

```yaml
- name: Install Kanidm Client
  hosts: all
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm-client
```

### Configure Unix Integration

```yaml
- name: Configure Kanidm Unixd
  hosts: kanidm_clients
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm-unixd
      kanidm_unixd_domain: "idm.example.com"
      kanidm_unixd_server: "https://idm.example.com"
```

## License

MIT

## Author Information

Kanidm Community Collection
