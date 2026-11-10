# (c) 2026 Nokia
#
# Licensed under the BSD 3 Clause license
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type  # pylint: disable=invalid-name

DOCUMENTATION = """
---
author: Sven Wisotzky (@wisotzky)
name: md
short_description: Cliconf plugin to configure and run CLI commands on Nokia SR OS devices (model-driven mode)
description:
  - This plugin provides low level abstraction APIs for sending CLI commands and
    receiving responses from Nokia SR OS network devices.
"""

# pylint: disable=wrong-import-position
import re
import json

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.common.text.converters import to_text
from ansible.plugins.cliconf import CliconfBase

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list


class Cliconf(CliconfBase):

    def get_device_operations(self):
        return {
            "supports_commit": True,
            "supports_rollback": True,
            "supports_defaults": True,
            "supports_onbox_diff": True,
            "supports_commit_comment": True,
            "supports_replace": True,

            "supports_multiline_delimiter": False,
            "supports_generate_diff": False,
            "supports_diff_replace": False,
            "supports_diff_match": False,
            "supports_diff_ignore_lines": False,

        }

    def get_sros_rpc(self):
        return [
            'get_capabilities',    # Retrieves device information and supported rpc methods
            'get_default_flag',    # CLI option to include defaults for config dumps
            'commit',              # Load configuration from candidate to running
            'discard_changes'      # Discard changes to candidate datastore
        ]

    def get_option_values(self):
        return {
            'format': ['text', 'flat', 'json', 'xml'],
            'diff_match': [],
            'diff_replace': [],
            'output': ['text']
        }

    def get_device_info(self):
        device_info = {}
        device_info['network_os'] = 'nokia.sros.md'
        device_info['network_os_platform'] = 'Nokia 7x50'

        reply = self.get('show system information')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'System Version\s+:\s+(.+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'System Type\s+:\s+(.+)', data)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'System Name\s+:\s+(.+)', data)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        match = re.search(r'Configuration Mode Oper:\s+(.+)', data)
        if match:
            device_info['sros_config_mode'] = match.group(1)
        else:
            device_info['sros_config_mode'] = 'classic'

        return device_info

    def get_capabilities(self):
        capabilities = super().get_capabilities()
        capabilities['device_operations'] = self.get_device_operations()
        capabilities['rpc'] += self.get_sros_rpc()
        capabilities['device_info'] = self.get_device_info()
        capabilities['network_api'] = 'cliconf'
        capabilities.update(self.get_option_values())
        return json.dumps(capabilities)

    def get_default_flag(self):
        return ['detail']

    def is_config_mode(self):
        """
        After a MD-CLI user has entered the edit-config command, the CLI
        session is in configuration mode. This is indicated by changing
        the MD-CLI context prompt (1st line) as following:

        (ex)[...] - exclusive mode (locked) for candidate configuration
        (gl)[...] - global (shared) mode for candidate configuration
        (pr)[...] - private mode for candidate configuration
        (ro)[...] - read-only mode

        Ansible does not expose different edit-config modes, while this
        plugin is using private mode to avoid interference with concurrent
        MD-CLI or NETCONF sessions.

        Note, that is Ansible module uses "edit-config private" and
        "quit-config" to enter and leave configuration mode. The
        alternative of using "configure private" is not supported.

        :return: True if session is running in configuration mode
        """

        prompt = self._connection.get_prompt().strip()
        return prompt.startswith(b'(')

    def is_classic_cli(self):
        """
        Determines if the session is running in Classic CLI or MD-CLI.
        Classic CLI uses a single line prompt while MD-CLI uses a multi
        line prompt. Setting is not static as it is possible to toggle
        between CLI engines:
          //             - toggle between modes
          /!md-cli       - set session to md-cli
          /!classic-cli  - set session to classic-cli

        It's also possible to execute single commands of the other
        engine by prepending the command with '//'.

        For integration purposes keep into consideration that MD mode
        and MD CLI are disabled by default. Please contact your Nokia
        SE/CE team to learn, if MD mode is supported on the platforms
        and releases used.

        :return: True if session is in classic CLI
        """

        prompt = self._connection.get_prompt().strip()
        return b'\n' not in prompt

    def enable_config_mode(self):
        if self.is_classic_cli():
            self.send_command('/!md-cli')

        self.send_command('exit all')

        if not self.is_config_mode():
            self.send_command('edit-config private')

    def is_classic_mode(self):
        reply = self.send_command('/show system information')
        data = to_text(reply, errors='surrogate_or_strict').strip()
        match = re.search(r'Configuration Mode Oper:\s+(.+)', data)
        return not match or match.group(1) == 'classic'

    # pylint: disable=arguments-renamed,redefined-builtin,too-many-branches
    def get_config(self, source='running', format='text', flags=None):
        # This Ansible module exits config-mode after any edit-config operation.
        # Therefore, accessing source='candidate' (when running in config-mode)
        # has been implemented for completeness only.
        #
        # Source 'active' and 'running' are equivalent. While 'running' covers
        # the 'persistent-indices { ... }' section too, 'active' covers only the
        # configuration itself.

        if flags is None:
            flags = []

        if source not in ('startup', 'candidate', 'running', 'intended', 'active'):
            raise ValueError(f"fetching configuration from {source} is not supported")

        if format not in self.get_option_values()['format']:
            valid = ','.join(self.get_option_values()['format'])
            raise ValueError(f"'format' value {format} is invalid. Valid values are {valid}")

        if self.is_classic_mode():
            raise ValueError("Nokia SROS node is running in classic mode. Use ansible_network_os=nokia.sros.classic")

        if self.is_classic_cli():
            self.send_command('/!md-cli')

        if source == 'startup' and self.is_config_mode():
            raise ValueError("fetching startup configuration in config mode is not supported")

        if source == 'candidate' and not self.is_config_mode():
            raise ValueError("fetching candidate configuration is only supported in config mode")

        if format != 'text':
            flags = [format] + flags

        if source == 'startup':
            self.enable_config_mode()
            self.send_command('configure')
            self.send_command('rollback startup')
            response = self.send_command(' '.join(['info'] + flags + ['/']))
            self.send_command('discard')
            self.send_command('exit all')
            self.send_command('quit-config')
        elif source == 'candidate':
            response = self.send_command(' '.join(['info'] + flags + ['/']))
        elif source == 'active':
            self.send_command('exit all')
            if not self.is_config_mode():
                self.send_command('edit-config read-only')
            response = self.send_command(' '.join(['info'] + flags + ['/']))
            self.send_command('exit all')
            self.send_command('quit-config')
        else:
            response = self.send_command(' '.join(['/admin show configuration', source] + flags))

        return response

    def edit_config(  # pylint: disable=arguments-differ,too-many-branches
        self, candidate=None, commit=True, replace=None, comment=None,
    ):
        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)

        if self.is_classic_mode():
            raise ValueError("Nokia SROS node is running in classic mode. Use ansible_network_os=nokia.sros.classic")

        self.enable_config_mode()

        requests = []
        responses = []

        try:
            if candidate:
                if replace:
                    cmd = 'delete configure'
                    requests.append(cmd)
                    responses.append(self.send_command(cmd))

                for cmd in to_list(candidate):
                    if isinstance(cmd, Mapping):
                        requests.append(cmd['command'])
                        responses.append(self.send_command(**cmd))
                    else:
                        requests.append(cmd)
                        responses.append(self.send_command(cmd))
            elif replace:
                # if replace from local file, copy to cflash first
                if not bool(re.match(r'^[cC][fF][12345]:', replace)):
                    self._connection.copy_file(source=replace, destination='ansible.cfg', proto='scp', timeout=30)
                    replace = 'ansible.cfg'

                self.send_command('configure')
                self.send_command(f'load full-replace {replace}'.strip())

            diffs = self.send_command('compare /').strip()

            if commit:
                if comment:
                    safe_comment = comment.replace('"', "'")
                    self.send_command(f'commit comment "{safe_comment}"')
                else:
                    self.send_command('commit')
            else:
                self.send_command('validate')
                self.send_command('discard')

            self.send_command('exit all')
            self.send_command('quit-config')

            if diffs:
                return {'request': requests, 'response': responses, 'diff': diffs}
            return {'request': requests, 'response': responses}

        except AnsibleConnectionFailure as exc:
            self.send_command('discard')
            self.send_command('exit all')
            self.send_command('quit-config')
            raise exc from exc

    # pylint: disable=arguments-renamed,too-many-arguments,too-many-positional-arguments
    def get(self, command, prompt=None, answer=None, sendonly=False, output=None, newline=True, check_all=False):
        if output:
            raise ValueError(f"'output' value {output} is not supported for get")

        return self.send_command(
            command=command,
            prompt=prompt,
            answer=answer,
            sendonly=sendonly,
            newline=newline,
            check_all=check_all,
        )

    def rollback(self, rollback_id, commit=True):
        if self.is_classic_mode():
            raise ValueError("Nokia SROS node is running in classic mode. Use ansible_network_os=nokia.sros.classic")

        self.enable_config_mode()

        try:
            self.send_command('configure')
            self.send_command(f'rollback {rollback_id}'.strip())

            diffs = self.send_command('compare /').strip()

            if commit:
                self.send_command('commit')
            else:
                self.send_command('validate')
                self.send_command('discard')

            self.send_command('exit all')
            self.send_command('quit-config')

            if diffs:
                return {'diff': diffs}
            return {}

        except AnsibleConnectionFailure as exc:
            self.send_command('discard')
            self.send_command('exit all')
            self.send_command('quit-config')
            raise exc from exc

    def commit(self):  # pylint: disable=arguments-differ
        if self.is_classic_cli():
            self.send_command('/!md-cli')

        if self.is_config_mode():
            self.send_command('commit')
            self.send_command('exit all')
            self.send_command('quit-config')

    def discard_changes(self):
        if self.is_classic_cli():
            self.send_command('/!md-cli')

        if self.is_config_mode():
            self.send_command('discard')
            self.send_command('exit all')
            self.send_command('quit-config')
