# (c) 2025 Nokia
#
# Licensed under the BSD 3 Clause license
# SPDX-License-Identifier: BSD-3-Clause

DOCUMENTATION = '''
---
module: device_info
author: Sven Wisotzky (@wisotzky)
short_description: Return device information
description:
  - Returns network OS, hostname, model, platform, software version and
    configuration mode of the connected Nokia SR OS device.
  - Works with the CLI (P(ansible.netcommon.network_cli#connection)) and NETCONF
    (P(ansible.netcommon.netconf#connection)) connections of this collection.
'''

EXAMPLES = '''
- name: get device info
  nokia.sros.device_info:
'''

RETURN = '''
output:
  description: device information gathered
  returned: success
  type: dict
  sample:
    network_os: "nokia.sros.classic"
    network_os_hostname: "Berlin"
    network_os_model: "7750 SR-12"
    network_os_version: "B-19.5.R2"
    sros_config_mode: "classic"
'''

# pylint: disable=wrong-import-position
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection


def main():
    argument_spec = {}
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    connection = Connection(module._socket_path)  # pylint: disable=protected-access

    device_info = connection.get_device_info() or {}
    warnings = device_info.pop('warnings', None)
    if warnings:
        if not isinstance(warnings, (list, tuple, set)):
            warnings = [warnings]
        for warning in warnings:
            if warning:
                module.warn(str(warning))

    module.exit_json(changed=False, output=device_info)


if __name__ == '__main__':
    main()
