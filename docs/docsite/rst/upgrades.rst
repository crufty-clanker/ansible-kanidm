.. _upgrades:

==========
Upgrades
==========

Kanidm requires sequential upgrades through each minor version. This document
explains how to upgrade safely using the Ansible collection.

.. note::

   The collection enforces sequential upgrades automatically. If you try to
   skip a minor version (e.g., 1.3 → 1.5), the role will refuse to proceed
   and instruct you to upgrade step-by-step.

Upgrade Path
===========

Kanidm's upgrade model is **linear by minor version**. Each minor release
introduces database changes that must be applied in order:

.. code-block:: text

   1.1.x → 1.2.x → 1.3.x → 1.4.x → 1.5.x ...

You **cannot** skip intermediate minor versions. This is a Kanidm requirement,
not a collection limitation.

How It Works
============

The ``kanidm_server`` role includes a pre-upgrade migration check that runs
**before** any downloads or service changes:

1. The role runs ``kanidmd domain upgrade-check`` against the running database
2. If the check passes, the role proceeds with downloading and installing the new version
3. If the check fails, no changes are made — the running service is untouched

This ensures you never end up in a state where the database is incompatible
with the new binary.

Sequential Upgrade Enforcement
==============================

The role detects when you're trying to skip a minor version:

.. code-block:: yaml
   :caption: tasks/detect-version-change.yml

   - name: Check for sequential upgrade requirement
     ansible.builtin.fail:
       msg: >-
         Kanidm requires sequential upgrades through each minor version.
         Current version: {{ _kanidm_running_version.stdout | default('unknown') }}
         Target version: {{ kanidm_version }}
         You must upgrade through intermediate versions first.
         Example: from 1.3.x, upgrade to 1.4.x, then 1.5.x.
         Update kanidm_version to the next minor version and re-run.
     when: >-
       _kanidm_version_changed | bool and
       ...

Example Upgrade Sequence
========================

Starting from Kanidm 1.3.x, upgrade to 1.5.0:

.. code-block:: bash

   # Step 1: Upgrade to 1.4.x
   ansible-playbook kanidm_server.yml -e "kanidm_server_version=1.4.0-1"

   # Step 2: Upgrade to 1.5.x
   ansible-playbook kanidm_server.yml -e "kanidm_server_version=1.5.0-1"

Each step:

1. Runs the upgrade check against the running database
2. Downloads the new binary
3. Installs the package (which replaces the binary)
4. Restarts the service

Fresh Install Detection
========================

The role automatically detects fresh installs. When no Kanidm binary exists,
the upgrade check is skipped entirely — there's nothing to protect.

.. code-block:: text

   Kanidm fresh install.
   Version: 1.1.0-1.
   Existing binary: no.

What to Do on Failure
======================

If the role fails with a sequential upgrade error:

1. **Do not** try to force the upgrade
2. **Check your current version**: ``kanidmd --version``
3. **Upgrade to the next minor version**: update ``kanidm_server_version``
   to the immediate next minor (e.g., 1.3.x → 1.4.x)
4. **Re-run the playbook**
5. **Repeat** until you reach your target version

Rollback
========

If an upgrade fails partway through:

1. **Stop the kanidm service**: ``systemctl stop kanidm``
2. **Restore the old binary**: ``dpkg --force-depends -i /path/to/old.deb``
3. **Restart the service**: ``systemctl start kanidm``

The Ansible role does not provide automated rollback — the operator must
manually restore the previous version if needed. This is by design, as
database upgrades are generally irreversible.
