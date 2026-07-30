# Integration Tests

This directory contains integration tests for the kanidm_community.kanidm collection.

## Running Integration Tests Locally

### Prerequisites

- Docker installed and running
- Python 3.11+
- Ansible-core
- community.docker collection (`ansible-galaxy collection install community.docker`)
- kanidm Python package (`pip install kanidm`)

### Setup

1. Start a Kanidm server container:

```bash
# Create certificates
mkdir -p /tmp/kanidm-certs
openssl req -x509 -newkey rsa:2048 -keyout /tmp/kanidm-certs/key.pem -out /tmp/kanidm-certs/chain.pem -days 365 -nodes -subj "/CN=kanidm.test"

# Start container
docker run -d \
  --name kanidm \
  -p 8443:8443 \
  -v /tmp/kanidm-certs:/data \
  kanidm/server:latest

# Wait for it to be ready
sleep 10
curl -sk https://localhost:8443/health
```

2. Set environment variables:

```bash
export KANIDM_SERVER="https://localhost:8443"
export KANIDM_ADMIN_PASSWORD="adminpassword"
export KANIDM_SKIP_TLS="true"
```

3. Run tests:

```bash
ansible-test integration --docker ubuntu
```

Or run specific tests:

```bash
ansible-test integration --docker ubuntu kanidm_auth
```

### Testing Binary Modules with Docker Connection Plugin

The `community.docker.docker` connection plugin allows running Ansible tasks directly inside Docker containers.

To test binary modules (kanidmd_*), use the Docker connection:

```bash
# Start Kanidm container
docker run -d \
  --name kanidm \
  -v /tmp/kanidm-certs:/data \
  kanidm/server:latest

# Install kanidm tools in the container
docker exec kanidm apk add --no-cache kanidm-tools

# Run tests with docker connection
ansible-playbook -i tests/integration/inventory.docker tests/integration/targets/kanidmd_backup/test.yml
```

The inventory file (`tests/integration/inventory.docker`) is configured with:
```
[docker]
kanidm ansible_connection=docker
```

### Cleanup

```bash
docker stop kanidm
docker rm kanidm
rm -rf /tmp/kanidm-certs
```

## Test Targets

Each test target has a `test.yml` file:

### HTTP API Modules (tested against running server)
- `kanidm_auth` — Authentication module
- `kanidm_group` — Group management
- `kanidm_person` — Person accounts
- `kanidm_service_account` — Service accounts
- `kanidm_ssh_key` — SSH key management
- `kanidm_api_token` — API tokens
- `kanidm_denied_names` — Denied names
- `kanidm_password_badlist` — Password badlist
- `kanidm_info` — Lookup plugin
- `kanidm_group_members` — Group members filter
- `kanidm_memberof` — User groups filter

### Binary Modules (tested via Docker connection)
- `kanidmd_backup` — Database backup
- `kanidmd_restore` — Database restore
- `kanidmd_reload` — Config reload
- `kanidmd_verify` — Database verification
- `kanidmd_domain` — Domain configuration
- `kanidmd_healthcheck` — Server health checks
- `kanidmd_disable_account` — Disable account
- `kanidmd_recover_account` — Recover account
- `kanidmd_vacuum` — Database vacuum
- `kanidmd_reindex` — Database reindex
- `kanidmd_configtest` — Configuration test

## Notes

- Integration tests require a running Kanidm server
- Tests clean up after themselves (delete created resources)
- HTTP API modules test against the server via HTTP
- Binary modules test via `community.docker.docker` connection plugin
- The Docker connection plugin requires `community.docker` collection
