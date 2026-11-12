# Reference

Generated from the plugin and module docstrings with `make docs`.

Each SR OS network OS is a set of plugins with the same name. Select it with `ansible_network_os`:

| Network OS | terminal | cliconf | netconf |
| --- | :---: | :---: | :---: |
| `nokia.sros.md` | [yes](nokia.sros.md_terminal.md) | [yes](nokia.sros.md_cliconf.md) | [yes](nokia.sros.md_netconf.md) |
| `nokia.sros.classic` | [yes](nokia.sros.classic_terminal.md) | [yes](nokia.sros.classic_cliconf.md) | – |
| `nokia.sros.light` | [yes](nokia.sros.light_terminal.md) | [yes](nokia.sros.light_cliconf.md) | – |

## Modules

- [`nokia.sros.device_info`](nokia.sros.device_info.md) - Return device information


## Cliconf plugins

- [`nokia.sros.classic`](nokia.sros.classic_cliconf.md) - Cliconf plugin to configure and run CLI commands on Nokia SR OS devices (classic mode)
- [`nokia.sros.light`](nokia.sros.light_cliconf.md) - Cliconf for Nokia SR OS classic mode without rollback support
- [`nokia.sros.md`](nokia.sros.md_cliconf.md) - Cliconf plugin to configure and run CLI commands on Nokia SR OS devices (model-driven mode)


## Netconf plugins

- [`nokia.sros.md`](nokia.sros.md_netconf.md) - Plugin to run NETCONF RPC on Nokia SR OS platform


## Terminal plugins

- [`nokia.sros.classic`](nokia.sros.classic_terminal.md) - Classic-CLI terminal support for Nokia SR OS devices
- [`nokia.sros.light`](nokia.sros.light_terminal.md) - Classic-CLI terminal support for Nokia SR OS devices
- [`nokia.sros.md`](nokia.sros.md_terminal.md) - MD-CLI terminal support for Nokia SR OS devices

