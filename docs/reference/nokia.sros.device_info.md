# nokia.sros.device_info module

**Return device information**

## Synopsis

* Returns network OS, hostname, model, platform, software version and configuration mode of the connected Nokia SR OS device.
* Works with the CLI ([`ansible.netcommon.network_cli`](https://docs.ansible.com/projects/ansible/latest/collections/ansible/netcommon/network_cli_connection.html)) and NETCONF ([`ansible.netcommon.netconf`](https://docs.ansible.com/projects/ansible/latest/collections/ansible/netcommon/netconf_connection.html)) connections of this collection.

## Examples

```yaml
- name: get device info
  nokia.sros.device_info:
```

## Return Values

| Key | Type | Comments |
| --- | --- | --- |
| output {#return-output} | dict | device information gathered<br/>**Returned:** success |

Sample of `output`:

```yaml
network_os: nokia.sros.classic
network_os_hostname: Berlin
network_os_model: 7750 SR-12
network_os_version: B-19.5.R2
sros_config_mode: classic
```


## Authors

* Sven Wisotzky (@wisotzky)

