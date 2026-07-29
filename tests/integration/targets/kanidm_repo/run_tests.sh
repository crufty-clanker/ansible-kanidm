#!/bin/bash
# Integration test for kanidm_repo role
# Run with: ansible-playbook -i inventory test.yml

set -e

ANSIBLE_ROLES_PATH="../../../roles" ansible-playbook test.yml -i inventory -v --check --diff
