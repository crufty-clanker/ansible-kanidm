<!--# cspell: ignore SSOT CMDB -->
# AGENTS.md

Ensure that all practices and instructions described by
<https://raw.githubusercontent.com/ansible/ansible-creator/refs/heads/main/docs/agents.md>
are followed.

## Dependabot

- Configure `.github/dependabot.yml` to keep GitHub Actions, Python, and pre-commit dependencies up to date
- Update GitHub Actions regularly to benefit from security patches and new features
- Review and merge Dependabot pull requests promptly, especially security updates
- Group related dependency updates to reduce PR noise (e.g., all Ansible-related actions together)
- Set a weekly update schedule for non-security updates
- Review update changelogs before merging major version updates
