# nokia.sros.md netconf plugin

**Plugin to run NETCONF RPC on Nokia SR OS platform**

Use with `ansible_network_os: nokia.sros.md`.

## Synopsis

* This Ansible plugin provides low-level abstraction APIs for executing commands and receiving responses via NETCONF on networking devices that run Nokia SR OS.
* To use this plugin, please ensure that the device is running in model-driven mode (aka MD MODE) and has the NETCONF protocol enabled.

## Parameters

| Parameter | Type | Comments |
| --- | --- | --- |
| ncclient_device_handler {#param-ncclient-device-handler} | str | Specifies the ncclient device-handler name for Nokia SR OS. Please refer to the ncclient library documentation for details.<br/>**Default:** `default` |

## Authors

* Sven Wisotzky (@wisotzky)

