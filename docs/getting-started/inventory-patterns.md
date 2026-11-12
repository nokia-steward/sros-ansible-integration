# Inventory Patterns

Set platform-specific variables in **group_vars** so playbooks stay the same for every router. The same snippets are shipped under `playbooks/examples/` with a sample inventory.

## Variables you set once

| Variable | Purpose |
| --- | --- |
| `ansible_network_os` | `nokia.sros.md`, `nokia.sros.classic` or `nokia.sros.light` |
| `ansible_connection` | `ansible.netcommon.network_cli` (CLI) or `ansible.netcommon.netconf` (NETCONF, `md` only) |
| `ansible_host` | Management address |
| `ansible_user`, `ansible_password` | SSH / NETCONF credentials — prefer [Ansible Vault](../guides/security-guide.md) |
| `ansible_private_key_file` | Optional SSH key instead of a password |

Passwords belong in vault, not in plain inventory. See the [Security Guide](../guides/security-guide.md).

## MD-CLI (model-driven)

```yaml
# group_vars/sros_md.yml
ansible_connection: ansible.netcommon.network_cli
ansible_network_os: nokia.sros.md
ansible_user: admin
ansible_password: "{{ vault_sros_password }}"
```

Enable NETCONF on the router if you use `ansible.netcommon.netconf`:

```text
/configure system management-interface netconf admin-state enable
```

```yaml
# group_vars/sros_md_netconf.yml
ansible_connection: ansible.netcommon.netconf
ansible_network_os: nokia.sros.md
ansible_user: admin
ansible_password: "{{ vault_sros_password }}"
```

## Classic CLI (with rollback)

```yaml
# group_vars/sros_classic.yml
ansible_connection: ansible.netcommon.network_cli
ansible_network_os: nokia.sros.classic
ansible_user: admin
ansible_password: "{{ vault_sros_password }}"
```

Configure a rollback location before using `cli_config` with diff and rollback-on-error. The integration playbook [sros_classic_cli_commission.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_classic_cli_commission.yml) shows one pattern.

Use `nokia.sros.light` when rollback is not available or not desired.

## Example inventory

```yaml
# inventory.yml
all:
  children:
    sros_md:
      hosts:
        pe1:
          ansible_host: 192.0.2.10
    sros_classic:
      hosts:
        pe2:
          ansible_host: 192.0.2.11
```

Point `group_vars/` at the child group names (`sros_md`, `sros_classic`, …) or use `ansible_group_priority` if groups overlap.

## Run a shipped playbook

```bash
ansible-playbook -i inventory.yml nokia.sros.device_inventory
```

Limit hosts with `-e target=sros_md` when needed.
