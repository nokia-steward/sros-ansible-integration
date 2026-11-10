# Playbooks

Workflow playbooks shipped with `nokia.sros`. Run them by name from any directory once the collection is installed:

```bash
ansible-playbook -i inventory.yml nokia.sros.<name> [-e variable=value ...]
```

Connection settings come from your inventory. Each playbook documents its variables in the header comment; `target` limits the run to a host pattern. Reports are written below the directory you run `ansible-playbook` from.

| Playbook | What it does | Main variables | Output |
| --- | --- | --- | --- |
| `device_inventory` | Hostname, model, platform, software version and configuration mode per router | `report_dir`, `target` | `reports/device_inventory.{csv,json}` |

## Examples

`examples/` contains an example inventory with group variables for MD-CLI, classic CLI and NETCONF. Copy it as a starting point:

```bash
cp -r ~/.ansible/collections/ansible_collections/nokia/sros/playbooks/examples my-sros-lab
cd my-sros-lab
ansible-playbook -i inventory.yml nokia.sros.device_inventory
```

See [Inventory Patterns](https://nokia-steward.github.io/sros-ansible-integration/getting-started/inventory-patterns/) for the variables and [Examples](https://nokia-steward.github.io/sros-ansible-integration/examples/) for integration playbooks in the repository.
