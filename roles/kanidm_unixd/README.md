# kanidm_community.kanidm.kanidm_unixd Role

Install and configure kanidm_unixd for PAM/SSSD integration on Debian-based systems.

## Requirements

- Debian-based system (Ubuntu 22.04+, Debian 12+)
- Ansible >= 2.15
- Kanidm server running and accessible

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `kanidm_unixd_version` | `"1.1.0-1"` | Kanidm-unixd version to install |
| `kanidm_unixd_distro_codename` | `""` | Distribution codename (auto-detected) |
| `kanidm_unixd_ppa_url` | `"https://kanidm.github.io/kanidm_ppa"` | PPA repository URL |
| `kanidm_unixd_ppa_component` | `"stable"` | PPA component (stable/nightly) |
| `kanidm_unixd_packages` | `["kanidm_unixd", "libnss-kanidm", "libpam-kanidm"]` | APT packages to install |
| `kanidm_unixd_domain` | `"idm.example.com"` | Kanidm domain name |
| `kanidm_unixd_server` | `"https://idm.example.com"` | Kanidm server URL |
| `kanidm_unixd_realmd_domain` | `"idm.example.com"` | Realm domain name |
| `kanidm_unixd_cache_timeout` | `3600` | Cache timeout in seconds |
| `kanidm_unixd_nss_enable` | `true` | Enable NSS integration |
| `kanidm_unixd_nss_groups` | `true` | Enable NSS groups |
| `kanidm_unixd_nss_extra_groups` | `true` | Enable NSS extra groups |
| `kanidm_unixd_pam_enable` | `true` | Enable PAM integration |
| `kanidm_unixd_pam_ssh` | `true` | Enable PAM SSH support |
| `kanidm_unixd_service_state` | `"started"` | Desired service state |
| `kanidm_unixd_service_enabled` | `true` | Enable on boot |

## Example Playbook

```yaml
- name: Install Kanidm Unixd
  hosts: kanidm_clients
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm_unixd
      kanidm_unixd_domain: "idm.example.com"
      kanidm_unixd_server: "https://idm.example.com"
```

## Idempotency

This role is idempotent. Running it multiple times will not produce changes on subsequent runs.

## License

MIT

## Author Information

Kanidm Community Collection
