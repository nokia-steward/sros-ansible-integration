# Quick Start

This guide sets up an inventory for SR OS routers and runs a first playbook over CLI and NETCONF. It assumes the [installation](installation.md) is complete. For a task-to-module overview first, see [Start Here](start-here.md).

## Prepare the router

The CLI plugins connect over SSH, which is enabled by default. For NETCONF, enable the NETCONF server on model-driven routers:

```text
/configure system management-interface netconf admin-state enable
/configure system management-interface netconf auto-config-save true
```

## Inventory

Set `ansible_network_os` per group to the [network OS](../guides/user-guide.md#network-os-modes) that matches the configuration mode of the router:

```yaml
# inventory.yml
all:
  vars:
    ansible_connection: ansible.netcommon.network_cli
    ansible_user: admin
    ansible_password: "{{ vault_sros_password }}"
  children:
    sros_md:
      vars:
        ansible_network_os: nokia.sros.md
      hosts:
        pe1:
          ansible_host: 192.0.2.10
    sros_classic:
      vars:
        ansible_network_os: nokia.sros.classic
      hosts:
        pe2:
          ansible_host: 192.0.2.11
```

Store passwords with [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html) rather than in plain text.

## First playbook: device information

```yaml
# device_info.yml
- hosts: all
  gather_facts: false
  tasks:
    - name: Get device info
      nokia.sros.device_info:
      register: device_info

    - name: Display device info
      ansible.builtin.debug:
        var: device_info.output
```

```bash
ansible-playbook -i inventory.yml device_info.yml
```

The module returns the network OS, hostname, model, platform, software version and configuration mode, for example:

```yaml
output:
  network_os: "nokia.sros.md"
  network_os_hostname: "pe1"
  network_os_model: "7750 SR-1"
  network_os_platform: "Nokia 7x50"
  network_os_version: "B-25.10.R1"
  sros_config_mode: "model-driven"
```

## Run commands and change configuration

```yaml
- hosts: sros_md
  gather_facts: false
  tasks:
    - name: Show system information
      ansible.netcommon.cli_command:
        command: show system information
      register: info

    - name: Change the system location
      ansible.netcommon.cli_config:
        config: |
          configure system
            location hamburg
            exit all
```

Run the playbook with `--check --diff` first to preview the change. The [User Guide](../guides/user-guide.md) describes how check mode and diff work per network OS.

## NETCONF

On `nokia.sros.md` routers, set the connection to NETCONF to use `ansible.netcommon.netconf_get` and friends:

```yaml
- hosts: sros_md
  gather_facts: false
  vars:
    ansible_connection: ansible.netcommon.netconf
  tasks:
    - name: Get system state
      ansible.netcommon.netconf_get:
        filter: <state xmlns="urn:nokia.com:sros:ns:yang:sr:state"><system/></state>
        display: native
      register: result

    - name: Display the software version
      ansible.builtin.debug:
        var: result.output.data.state.system.version
```

More playbooks are listed in [Examples](../examples.md).
