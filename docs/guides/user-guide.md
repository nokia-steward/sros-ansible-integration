# User Guide

## Network OS modes

Select the network OS per host with `ansible_network_os`:

```yaml
ansible_network_os: nokia.sros.<mode>
```

| Network OS | Use for | Connections |
| --- | --- | --- |
| `nokia.sros.md` | Routers in model-driven configuration mode, using MD-CLI | `ansible.netcommon.network_cli`, `ansible.netcommon.netconf` |
| `nokia.sros.classic` | Routers in classic configuration mode, with rollback configured | `ansible.netcommon.network_cli` |
| `nokia.sros.light` | Routers in classic configuration mode, without rollback | `ansible.netcommon.network_cli` |

The [`nokia.sros.device_info`](../reference/nokia.sros.device_info.md) module reports the configuration mode of a router as `sros_config_mode`.

## Model-Driven Mode

In **model-driven** mode, the `nokia.sros.md` cliconf plugin uses MD-CLI candidate configuration:

* Configuration changes are loaded with `edit-config private`, so concurrent MD-CLI or NETCONF sessions do not interfere.
* `changed` and `diff` are populated from `compare /` of the candidate against the running configuration.
* With `--check`, the candidate configuration is validated and discarded without commit.
* `ansible.netcommon.cli_config` supports commit comments (`commit_comment`), `rollback` and `replace`. `replace` accepts a file on the router (`cf3:/...`) or a local file, which is copied to the router with SCP before `load full-replace`.
* `get_config()` supports the sources `running`, `active`, `intended`, `startup` and `candidate`, in the formats `text`, `flat`, `json` and `xml`.

If a router runs in classic mode, the plugin fails with a hint to use `nokia.sros.classic`.

## Classic Mode

In **Classic CLI** mode, the plugin leverages the SR OS built-in **rollback** feature.
Ensure that rollback storage is properly configured, for example:

```text
A:Antwerp# file md cf3:/rollbacks
*A:Antwerp# configure system rollback rollback-location cf3:/rollbacks/config
INFO: CLI No checkpoints currently exist at the rollback location.
*A:Antwerp# admin rollback save
Saving rollback configuration to cf3:/rollbacks/config.rb... OK
*A:Antwerp#
```

!!! note
    Use `nokia.sros.light` for nodes that do not support rollback or where rollback usage is undesired.

### Snapshot / Rollback Workflow

* A temporary rollback checkpoint is created at the start of each `cli_config` operation.
* If a configuration error occurs, the plugin reverts to the pre-operation checkpoint (**rollback-on-error**).
* If successful, the plugin compares the new configuration to the previous checkpoint to populate `changed` and `diff` results.
* With the `--check` (dry-run) option, configuration changes are applied, validated, and then immediately rolled back — providing syntax checks and diff output.
* After completion, the temporary checkpoint is deleted to keep rollback history clean.

!!! warning
    * Dry-run temporarily activates configuration changes before rolling them back. Be aware that this can cause brief service impact.
    * `rollback-on-error` may have side effects on modules such as BGP within VPRNs, which revert to default state (`shutdown`) before rollback is applied. Refer to the *Basic System Configuration Guide* for details.

### Restrictions

* Some platforms may not support checkpoint/rollback.
* All changes are written directly to the running configuration.
* Operation type `replace` is not supported.
* The oldest rollback checkpoint may be deleted after plugin execution.

## Light Mode

The **Light Mode** (`nokia.sros.light`) is a simplified CLI implementation used when rollback is not available or not desired.
It determines configuration changes based on the **prompt change indicator** (appearance of `*` in the prompt).

### Restrictions

* If the device already has unsaved changes before a task runs, the playbook will treat it as `changed`.
* `--diff` and `--check` modes are not supported.

## Device information

[`nokia.sros.device_info`](../reference/nokia.sros.device_info.md) works with both CLI and NETCONF connections:

```yaml
output:
  network_os: "nokia.sros.classic"
  network_os_hostname: "Antwerp"
  network_os_model: "7750 SR-12"
  network_os_platform: "Nokia 7x50"
  network_os_version: "B-19.5.R2"
  sros_config_mode: "classic"
```
