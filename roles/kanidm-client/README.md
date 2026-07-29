# kanidm_community.kanidm.kanidm-client Role

Install Kanidm client CLI tools from the official PPA.

## Requirements

- Debian-based system (Ubuntu 22.04+, Debian 12+)
- Ansible >= 2.15

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `kanidm_client_version` | `"1.1.0-1"` | Kanidm client version to install |
| `kanidm_client_distro_codename` | `""` | Distribution codename (auto-detected) |
| `kanidm_client_ppa_url` | `"https://kanidm.github.io/kanidm_ppa"` | PPA repository URL |
| `kanidm_client_ppa_component` | `"stable"` | PPA component (stable/nightly) |
| `kanidm_client_packages` | `["kanidm-tools"]` | APT packages to install |

## Example Playbook

```yaml
- name: Install Kanidm client
  hosts: all
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm-client
```

## Idempotency

This role is idempotent. Running it multiple times will not produce changes on subsequent runs.

## License

MIT

## Author Information

Kanidm Community Collection
