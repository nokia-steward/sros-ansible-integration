# (c) 2025 Nokia
#
# Licensed under the BSD 3 Clause license
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type  # pylint: disable=invalid-name

DOCUMENTATION = """
---
author: Sven Wisotzky (@wisotzky)
name: md
short_description: Plugin to run NETCONF RPC on Nokia SR OS platform
description:
  - This Ansible plugin provides low-level abstraction APIs for executing commands
    and receiving responses via NETCONF on networking devices that run Nokia SR OS.
  - To use this plugin, please ensure that the device is running in model-driven
    mode (aka MD MODE) and has the NETCONF protocol enabled.
options:
  ncclient_device_handler:
    type: str
    default: default
    description:
      - Specifies the ncclient device-handler name for Nokia SR OS. Please refer to
        the ncclient library documentation for details.
"""

# pylint: disable=wrong-import-position
import json

from ansible.module_utils.common.text.converters import to_text
from ansible.plugins.netconf import NetconfBase
from ansible.plugins.netconf import ensure_ncclient

try:
    from ncclient.xml_ import to_ele
except ImportError:
    pass  # ensure_ncclient raises a clear error when ncclient is missing


class Netconf(NetconfBase):
    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            return None

    @ensure_ncclient
    def get_device_info(self):
        device_info = {}
        device_info['network_os'] = 'nokia.sros.md'
        device_info['network_os_platform'] = 'Nokia 7x50'

        xmlns = "urn:nokia.com:sros:ns:yang:sr:state"
        state_filter = (
            f'<state xmlns="{xmlns}"><system><platform/><bootup/><version/>'
            f'<lldp/><management-interface/></system></state>'
        )
        reply = to_ele(self.m.get(filter=('subtree', state_filter)).data_xml)

        device_info['network_os_hostname'] = reply.findtext(
            f'.//{{{xmlns}}}state/{{*}}system/{{*}}lldp/{{*}}system-name'
        )
        device_info['network_os_version'] = reply.findtext(
            f'.//{{{xmlns}}}state/{{*}}system/{{*}}version/{{*}}version-number'
        )
        device_info['network_os_model'] = reply.findtext(f'.//{{{xmlns}}}state/{{*}}system/{{*}}platform')
        device_info['sros_config_mode'] = reply.findtext(
            f'.//{{{xmlns}}}state/{{*}}system/{{*}}management-interface/{{*}}configuration-oper-mode'
        )

        return device_info

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'netconf'
        result['device_info'] = self.get_device_info()
        result['server_capabilities'] = list(self.m.server_capabilities)
        result['client_capabilities'] = list(self.m.client_capabilities)
        result['session_id'] = self.m.session_id
        result['device_operations'] = self.get_device_operations(result['server_capabilities'])
        return json.dumps(result)
