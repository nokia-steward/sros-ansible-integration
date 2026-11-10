![NOKIA](media/logo.png)

---

# Ansible Collection – `nokia.sros`

[![CI](https://github.com/nokia-steward/sros-ansible-integration/actions/workflows/ci.yml/badge.svg)](https://github.com/nokia-steward/sros-ansible-integration/actions/workflows/ci.yml)
[![Ansible Galaxy](https://img.shields.io/ansible/collection/v/nokia/sros?logo=ansible&logoColor=white)](https://galaxy.ansible.com/ui/repo/published/nokia/sros/)
[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue)](https://nokia-steward.github.io/sros-ansible-integration/)
[![License](https://img.shields.io/badge/license-BSD%203--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Ansible](https://img.shields.io/badge/ansible--core-2.20%2B-blue)](https://docs.ansible.com/)

The [Ansible](https://docs.ansible.com/ansible/latest/network/index.html) [`nokia.sros` collection](https://galaxy.ansible.com/ui/repo/published/nokia/sros) provides **CLI** and **[NETCONF](https://www.rfc-editor.org/rfc/rfc6241.html)** plugins for Nokia **SR OS** devices.
These plugins act as device drivers enabling the use of Ansible networking modules such as `cli_config` and `cli_command` from the [`ansible.netcommon` collection](https://docs.ansible.com/ansible/latest/collections/ansible/netcommon/index.html).
The collection also provides device information and capability discovery.

This project is a **Nokia-initiated open-source effort**, licensed under the [BSD 3-Clause License](LICENSE), designed to promote programmable network automation using standard IT tools.
We welcome contributions from the community — including tutorials, real-world playbook examples, feature requests, bug reports, or code enhancements.

> **Notes**
>
> * Ansible collections are distributed via [Ansible Galaxy](https://galaxy.ansible.com/).
> * For Nokia SR Linux and data-center switches, use the [`nokia.srlinux`](https://galaxy.ansible.com/ui/repo/published/nokia/srlinux) collection.
> * For OpenConfig [gNMI](https://github.com/openconfig/reference/blob/master/rpc/gnmi/gnmi-specification.md), gNOI and gNSI automation, use the [`nokia.openconfig`](https://galaxy.ansible.com/ui/repo/published/nokia/openconfig) collection.

---

## Requirements

* **Ansible Core** 2.20 or newer (2.22 recommended)
* **Python** 3.12 or newer on the controller (3.13 recommended)
* **Python libraries:** [ansible-pylibssh](https://pypi.org/project/ansible-pylibssh) ≥ 1.3.0, [jxmlease](https://pypi.org/project/jxmlease) ≥ 1.0.3, [ncclient](https://pypi.org/project/ncclient) ≥ 0.6.19
* **Collections:** [`ansible.netcommon`](https://galaxy.ansible.com/ui/repo/published/ansible/netcommon) ≥ 5.2.0, [`ansible.utils`](https://galaxy.ansible.com/ui/repo/published/ansible/utils) ≥ 3.0.0 (installed with the collection)

Older Ansible and Python releases no longer receive security fixes, see [Supported Ansible and Python versions](https://nokia-steward.github.io/sros-ansible-integration/support/#supported-ansible-and-python-versions).

---

## Supported SR OS Versions

Tested with **SR OS 25.7** and **25.10**.
Other versions may work but have not been explicitly validated.

---

## Installation

Use the following recipe to create a ready-to-use virtual environment for SR OS Ansible automation:

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install 'ansible-core>=2.20' 'ansible-pylibssh>=1.3.0' 'jxmlease>=1.0.3' 'ncclient>=0.6.19'

ansible-galaxy collection install nokia.sros
```

`ansible-galaxy` does not install Python libraries; install them into the same Python environment as Ansible. See the [Installation guide](https://nokia-steward.github.io/sros-ansible-integration/getting-started/installation/) for GitHub releases, execution environments and source builds.

---

## Quick example

```yaml
- name: Device information
  hosts: sros_routers
  gather_facts: false
  vars:
    ansible_connection: ansible.netcommon.network_cli
    ansible_network_os: nokia.sros.md
  tasks:
    - name: Get device info
      nokia.sros.device_info:
      register: device_info

    - name: Display device info
      ansible.builtin.debug:
        var: device_info.output
```

Set **`ansible_network_os`** to `nokia.sros.md`, `nokia.sros.classic` or `nokia.sros.light`. Use [`ansible.netcommon`](https://docs.ansible.com/ansible/latest/collections/ansible/netcommon/index.html) modules for commands and configuration, or run the shipped playbook `nokia.sros.device_inventory` for a fleet report.

Detailed tutorials are on the **[Nokia Network Developer Portal](https://network.developer.nokia.com/sr/learn/sr-os-ansible)**.

---

## Documentation

Full user documentation is published with **MkDocs** on GitHub Pages:

**https://nokia-steward.github.io/sros-ansible-integration/**

| Section | Description |
| --- | --- |
| [Start Here](https://nokia-steward.github.io/sros-ansible-integration/getting-started/start-here/) | Network OS, connection and modules for a task |
| [Installation](https://nokia-steward.github.io/sros-ansible-integration/getting-started/installation/) | Python dependencies, Galaxy, GitHub release, execution environments, source build |
| [Quick Start](https://nokia-steward.github.io/sros-ansible-integration/getting-started/quick-start/) | Inventory and first playbooks for MD-CLI, classic CLI and NETCONF |
| [Inventory Patterns](https://nokia-steward.github.io/sros-ansible-integration/getting-started/inventory-patterns/) | Group variables for MD-CLI, classic CLI and NETCONF |
| [User Guide](https://nokia-steward.github.io/sros-ansible-integration/guides/user-guide/) | Network OS modes, rollback, check mode and diff |
| [Security Guide](https://nokia-steward.github.io/sros-ansible-integration/guides/security-guide/) | Vault, SSH keys and controller hygiene |
| [Developer Guide](https://nokia-steward.github.io/sros-ansible-integration/guides/developer-guide/) | Development environment, sanity and containerlab tests |
| [Reference](https://nokia-steward.github.io/sros-ansible-integration/reference/) | Plugins and modules (from docstrings) |
| [Examples](https://nokia-steward.github.io/sros-ansible-integration/examples/) | Shipped workflow playbooks and the integration suite |

Build docs locally:

```bash
make install-dev
make docs
make docs-serve   # http://127.0.0.1:8000
```

---

## Plugins

| Network OS         | terminal | cliconf | netconf |
| ------------------ | :------: | :-----: | :-----: |
| nokia.sros.md      |     ✅    |    ✅    |    ✅    |
| nokia.sros.classic |     ✅    |    ✅    |    –    |
| nokia.sros.light   |     ✅    |    ✅    |    –    |

## Modules

The module **`nokia.sros.device_info`** retrieves information about the connected SR OS device.
It works with both CLI and NETCONF connections.

**Playbooks:** run with `ansible-playbook -i inventory.yml nokia.sros.<name>`, for example `nokia.sros.device_inventory`. See [playbooks/README.md](playbooks/README.md).

---

## Support

- [Documentation site](https://nokia-steward.github.io/sros-ansible-integration/)
- [Issues](https://github.com/nokia-steward/sros-ansible-integration/issues)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)

---

**Version:** 2.2.0 · **License:** BSD 3-Clause
