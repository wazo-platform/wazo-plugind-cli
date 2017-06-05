#!/usr/bin/env python3
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import sys

from xivo.cli import Interpreter
from xivo.token_renewer import TokenRenewer
from wazo_plugind_client import Client as PlugindClient
from xivo_auth_client import Client as AuthClient
from .config import load_config
from . import command


def _new_auth_client(config):
    auth_config = dict(config['auth'])
    username = auth_config.pop('service_id')
    password = auth_config.pop('service_key')
    del auth_config['key_file']
    return AuthClient(username=username, password=password, **auth_config)


def main():
    config = load_config(sys.argv[1:])

    token_renewer = TokenRenewer(_new_auth_client(config), expiration=600)
    plugind_client = PlugindClient(**config['plugind'])

    interpreter = Interpreter(prompt='wazo-plugind-cli> ',
                              history_file='~/.wazo_plugind_cli_history')
    interpreter.add_command('install', command.InstallCommand(plugind_client, config))
    interpreter.add_command('uninstall', command.UninstallCommand(plugind_client, config))

    token_renewer.subscribe_to_token_change(plugind_client.set_token)
    command_name = config.get('command')
    with token_renewer:
        if command_name:
            interpreter.execute_command_line(command_name)
        else:
            interpreter.loop()


if __name__ == '__main__':
    main()
