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

## Commit Changes

- Commit all changes after a change with a clear, descriptive commit message
- Use conventional commit format: `type(scope): description`
- Example: `feat(modules): add kanidm_group module for group management`
- Stage all modified and new files before committing
- Run pre-commit hooks before committing if available
- Do not commit build artifacts, .venv, or sensitive files

## Authoritative Sources

Do **not** assume Kanidm behavior from the `idm` CLI help output alone — the HTTP API may differ.
Always verify against the source of truth below.

### Kanidm Server (the project this collection manages)

| What | Where |
|------|-------|
| Source code | <https://github.com/kanidm/kanidm> |
| HTTP API (v1) | REST endpoints under `/v1/auth`, `/v1/group`, `/v1/person`, `/v1/service_account`, `/v1/oauth2`, `/v1/system`, `/v1/domain` — verified via pykanidm source |
| Auth flow | 3-step async: `POST /v1/auth` with `{"step":{"init":username}}` → `{"step":{"begin":"password"}}` → `{"step":{"cred":{"password":...}}}` → returns JWS token in `x-kanidm-auth-session-id` header |
| Data model | `person` = human user (has `displayname`, `memberof`, `classes`); `service_account` = machine identity (same shape, different endpoint) |

### pykanidm (official Python client library)

| What | Where |
|------|-------|
| Source | <https://github.com/kanidm/kanidm/tree/main/client> (inside the main kanidm repo) |
| PyPI | <https://pypi.org/project/pykanidm/> (package imports as `kanidm`, **not** `pykanidm`) |
| Nature | **Official** client library maintained by the Kanidm project team |
| Async | **All methods are `async def`** — Ansible modules must wrap calls with `asyncio.run()` or a running event loop |
| Key files | `kanidm/__init__.py` (KanidmClient class, all API methods), `kanidm/types.py` (pydantic models for responses), `kanidm/exceptions.py` (error classes), `kanidm/tokens.py` (JWS token parsing) |
| Endpoints | `kanidm.Endpoints` class — `AUTH`, `GROUP`, `OAUTH2`, `PERSON`, `SYSTEM`, `DOMAIN`, `SERVICE_ACCOUNT` |

### Ansible Collection (this project)

| What | Where |
|------|-------|
| Source (this repo) | `crufty-clanker/ansible-kanidm` (per `galaxy.yml` `repository` field) |
| Galaxy namespace | `kanidm_community.kanidm` |
| Roles | `roles/kanidm_repo`, `roles/kanidm_client`, `roles/kanidm_server`, `roles/kanidm_unixd` |

### What is NOT verified (do not assume)

- The exact Kanidm documentation URLs at kanidm.com — the site structure changes between versions and paths tried (e.g. `/cli/stable/`, `/server/stable/...`) have returned 404s.
- The full set of LDAP attributes the server accepts — only what pykanidm exposes is confirmed.
- That all roles are fully tested end-to-end — tests exist but coverage is incomplete.
- pykanidm type hints reflect actual server behavior — always verify against the server if possible.
