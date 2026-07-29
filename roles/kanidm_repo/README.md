# kanidm_community.kanidm.kanidm_repo Role

Set up the Kanidm PPA repository on Debian-based systems.

## Requirements

- Debian-based system (Ubuntu 22.04+, Debian 12+)
- Ansible >= 2.15

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `kanidm_repo_distro_codename` | `""` | Distribution codename (auto-detected) |
| `kanidm_repo_url` | `"https://kanidm.github.io/kanidm_ppa"` | PPA repository URL |
| `kanidm_repo_component` | `"stable"` | PPA component (stable/nightly) |
| `kanidm_repo_gpg_key_file` | `"kanidm_ppa.gpg"` | GPG key filename |
| `kanidm_repo_gpg_key_dest` | `"/etc/apt/trusted.gpg.d/kanidm_ppa.gpg"` | GPG key destination |
| `kanidm_repo_sources_list` | `"/etc/apt/sources.list.d/kanidm_ppa.list"` | Sources list path |

## Example Playbook

```yaml
- name: Set up Kanidm repository
  hosts: all
  become: true
  roles:
    - role: kanidm_community.kanidm.kanidm_repo
```

## Idempotency

This role is idempotent. Running it multiple times will not produce changes on subsequent runs.

## License

MIT

## Author Information

Kanidm Community Collection
