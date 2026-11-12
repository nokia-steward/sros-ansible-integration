# Start Here

The collection is mostly **network OS plugins** plus one module. Pick the network OS and connection for each host; tasks then use modules from [`ansible.netcommon`](https://docs.ansible.com/ansible/latest/collections/ansible/netcommon/index.html).

## Pick your task

| I want to… | Use | Notes |
| --- | --- | --- |
| See what network OS and SR OS release a router runs | [`nokia.sros.device_info`](../reference/nokia.sros.device_info.md) | CLI or NETCONF |
| Run a show command or MD-CLI / classic CLI | [`ansible.netcommon.cli_command`](https://docs.ansible.com/ansible/latest/collections/ansible/netcommon/cli_command_module.html) | `ansible_connection: ansible.netcommon.network_cli` |
| Change configuration with check mode and diff | [`ansible.netcommon.cli_config`](https://docs.ansible.com/ansible/latest/collections/ansible/netcommon/cli_config_module.html) | MD-CLI or classic; see [User Guide](../guides/user-guide.md) |
| Back up configuration to the controller | [`ansible.netcommon.cli_backup`](https://docs.ansible.com/ansible/latest/collections/ansible/netcommon/cli_backup_module.html) | MD-CLI and classic |
| Read YANG state over NETCONF | [`ansible.netcommon.netconf_get`](https://docs.ansible.com/ansible/latest/collections/ansible/netcommon/netconf_get_module.html) | `nokia.sros.md` only |
| Build a CSV/JSON inventory of many routers | Shipped playbook `nokia.sros.device_inventory` | [Examples](../examples.md#shipped-playbooks) |

For **gNMI, gNOI or gNSI**, use the [`nokia.openconfig`](https://nokia-steward.github.io/openconfig-ansible-integration/getting-started/start-here/) collection instead.

## Pick the network OS

| `ansible_network_os` | When |
| --- | --- |
| `nokia.sros.md` | Model-driven configuration (MD-CLI); supports NETCONF |
| `nokia.sros.classic` | Classic CLI with rollback configured |
| `nokia.sros.light` | Classic CLI without rollback |

Details: [User Guide](../guides/user-guide.md#network-os-modes).

## Next steps

1. [Installation](installation.md) — Python packages and the collection.
2. [Inventory Patterns](inventory-patterns.md) — group variables per mode.
3. [Quick Start](quick-start.md) — first playbook.
4. [Examples](../examples.md) — shipped and integration playbooks.
