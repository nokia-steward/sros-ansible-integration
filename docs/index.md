# Nokia SR OS Ansible Collection

Welcome to the documentation of the Ansible collection `nokia.sros`.

This collection provides **CLI** and **[NETCONF](https://www.rfc-editor.org/rfc/rfc6241.html)** plugins for Nokia **SR OS** devices. The plugins act as device drivers for the network modules of the [`ansible.netcommon`](https://docs.ansible.com/ansible/latest/collections/ansible/netcommon/index.html) collection, such as `cli_command`, `cli_config`, `cli_backup` and `netconf_get`. The collection also provides device information and capability discovery.

## What is included

### Network OS plugins

Each SR OS network OS is a set of plugins with the same name. Select it per host with `ansible_network_os`:

| Network OS | CLI engine | terminal | cliconf | netconf |
| --- | --- | :---: | :---: | :---: |
| [`nokia.sros.md`](reference/nokia.sros.md_cliconf.md) | MD-CLI (model-driven mode) | ✅ | ✅ | ✅ |
| [`nokia.sros.classic`](reference/nokia.sros.classic_cliconf.md) | Classic CLI with rollback | ✅ | ✅ | – |
| [`nokia.sros.light`](reference/nokia.sros.light_cliconf.md) | Classic CLI without rollback | ✅ | ✅ | – |

See the [User Guide](guides/user-guide.md) for the differences between the modes.

### Modules

- [`nokia.sros.device_info`](reference/nokia.sros.device_info.md) — network OS, hostname, model, platform, software version and configuration mode of the connected device, over CLI or NETCONF.

## Getting started

1. [Start Here](getting-started/start-here.md) — which network OS, connection and modules to use.
2. [Installation](getting-started/installation.md) — Python environment, external dependencies and the collection.
3. [Inventory Patterns](getting-started/inventory-patterns.md) — group variables for MD-CLI, classic CLI and NETCONF.
4. [Quick Start](getting-started/quick-start.md) — inventory and first playbooks for MD-CLI, classic CLI and NETCONF.
5. [User Guide](guides/user-guide.md) — network OS modes, rollback, check mode and diff.
6. [Reference](reference/index.md) — plugin and module documentation, generated from the sources.

Detailed tutorials are available on the [Nokia Network Developer Portal](https://network.developer.nokia.com/sr/learn/sr-os-ansible).

## Related collections

- [`nokia.openconfig`](https://nokia-steward.github.io/openconfig-ansible-integration/) — OpenConfig gNMI, gNOI and gNSI for SR OS and SR Linux.
- [`nokia.nsp`](https://nokia-steward.github.io/nsp-ansible-integration/) — Nokia Network Services Platform (NSP).
- [`nokia.srlinux`](https://galaxy.ansible.com/ui/repo/published/nokia/srlinux) — Nokia SR Linux.

## Support

- [Examples](examples.md) — shipped workflow playbooks and the integration test suite.
- [Support](support.md) — community, supported versions and testing before production.
- [Changelog](https://github.com/nokia-steward/sros-ansible-integration/blob/master/CHANGELOG.md) on GitHub.

---

**Collection version:** 2.2.0 · **License:** BSD 3-Clause · **Ansible Core:** 2.20+ (2.22 recommended) · **Python:** 3.12+ (3.13 recommended)
