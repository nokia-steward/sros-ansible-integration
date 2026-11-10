# Examples

## Shipped playbooks

The playbooks in [`playbooks/`](https://github.com/nokia-steward/sros-ansible-integration/tree/master/playbooks) are installed with the collection. Run them by name from any directory:

```bash
ansible-playbook -i inventory.yml nokia.sros.<name> [-e variable=value ...]
```

They read connection settings from the inventory; see [Inventory Patterns](getting-started/inventory-patterns.md). Example group variables ship under `playbooks/examples/`.

| Playbook | Description | Output |
| --- | --- | --- |
| [device_inventory](https://github.com/nokia-steward/sros-ansible-integration/blob/master/playbooks/device_inventory.yml) | Hostname, model, platform, software version and configuration mode per host | `reports/device_inventory.{csv,json}` |

```bash
ansible-playbook -i inventory.yml nokia.sros.device_inventory
ansible-playbook -i inventory.yml nokia.sros.device_inventory -e target=sros_md
```

## Integration test playbooks

The repository contains sample playbooks in [`tests/playbooks/`](https://github.com/nokia-steward/sros-ansible-integration/tree/master/tests/playbooks). They also serve as the integration test suite, see the [Developer Guide](guides/developer-guide.md#integration-tests) and [tests/README.md](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/README.md).

### NETCONF

| Playbook | Description |
| --- | --- |
| [sros_nc_state_demo.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_nc_state_demo.yml) | Read system state with `ansible.netcommon.netconf_get` |
| [sros_nc_device_info.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_nc_device_info.yml) | `nokia.sros.device_info` over NETCONF |

### Device Info

| Playbook | Description |
| --- | --- |
| [sros_cli_device_info.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_cli_device_info.yml) | `nokia.sros.device_info` over CLI, for MD-CLI and classic CLI routers |

### MD-CLI

| Playbook | Description |
| --- | --- |
| [sros_mdcli_command_demo.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_mdcli_command_demo.yml) | `cli_command` with CLI engine switching and prompts |
| [sros_mdcli_config_demo.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_mdcli_config_demo.yml) | `cli_config` change, rollback and backup |
| [sros_mdcli_bulk_demo.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_mdcli_bulk_demo.yml) | Bulk configuration from Jinja2 templates |
| [sros_mdcli_backup_restore_demo.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_mdcli_backup_restore_demo.yml) | `cli_backup` and restore with `cli_config` `replace` |

### Classic CLI

| Playbook | Description |
| --- | --- |
| [sros_classic_cli_commission.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_classic_cli_commission.yml) | Prepare a classic router (rollback location) |
| [sros_classic_cli_command_demo.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_classic_cli_command_demo.yml) | `cli_command` on classic CLI |
| [sros_classic_cli_config_demo.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_classic_cli_config_demo.yml) | `cli_config` change and backup |
| [sros_classic_cli_backup_restore_demo.yml](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks/sros_classic_cli_backup_restore_demo.yml) | `cli_backup` and restore attempt on classic CLI |

### Running integration tests

Categories are defined in [`tests/playbooks.yml`](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/playbooks.yml). With containerlab:

```bash
cd tests
./run.sh deploy
./run.sh run --category all --quiet --all
./run.sh destroy
```

The default `tests/ansible.cfg` uses inventory generated under `tests/clab-ansible/` on deploy. For your own routers, copy [`tests/inventory.example.yml`](https://github.com/nokia-steward/sros-ansible-integration/blob/master/tests/inventory.example.yml) to `tests/inventory.yml`.

See also [Quick Start](getting-started/quick-start.md) and the [User Guide](guides/user-guide.md).
