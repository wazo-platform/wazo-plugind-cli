#!/usr/bin/env python3
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import sys
import kombu

from xivo.cli import BaseCommand, Interpreter, UsageError
from xivo.token_renewer import TokenRenewer
from wazo_plugind_client import Client as PlugindClient
from xivo_auth_client import Client as AuthClient
from .config import load_config
from .bus import ProgressConsumer


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
    interpreter.add_command('install', InstallCommand(plugind_client, config))
    interpreter.add_command('uninstall', UninstallCommand(plugind_client, config))

    token_renewer.subscribe_to_token_change(plugind_client.set_token)
    command = config.get('command')
    with token_renewer:
        if command:
            interpreter.execute_command_line(command)
        else:
            interpreter.loop()


class BasePlugindCommand(BaseCommand):

    def __init__(self, client):
        super().__init__()
        self._client = client

    def execute(self):
        raise NotImplementedError()


class BaseAsyncCommand(BasePlugindCommand):

    def __init__(self, plugind_client, config):
        super().__init__(plugind_client)
        self.amqp_url = 'amqp://{username}:{password}@{host}:{port}//'.format(**config['bus'])
        self.exchange = kombu.Exchange(config['bus']['exchange_name'],
                                       config['bus']['exchange_type'])

    def execute(self, *args):
        async = args[-1]
        if async:
            self.execute_async(*args[:-1])
        else:
            self.execute_sync(*args[:-1])

    def execute_sync(self, *args):
        result = self.execute_async(*args)
        routing_key = self.routing_key_fmt.format(result['uuid'])

        with kombu.Connection(self.amqp_url) as conn:
            ProgressConsumer(conn, routing_key, self.exchange).run()


class InstallCommand(BaseAsyncCommand):

    help = 'Install a plugin'
    usage = '<method> <plugin> [--async]'
    routing_key_fmt = 'plugin.install.{}.*'

    def prepare(self, command_args):
        try:
            method = command_args[0]
            plugin = command_args[1]
            async = len(command_args) > 2 and command_args[2] == '--async'
            return method, plugin, async
        except Exception:
            raise UsageError()

    def execute_async(self, method, plugin):
        return self._client.plugins.install(plugin, method)


class UninstallCommand(BaseAsyncCommand):

    help = 'Uninstall a plugin'
    usage = '<namespace>/<name> [--async]'
    routing_key_fmt = 'plugin.uninstall.{}.*'

    def prepare(self, command_args):
        try:
            namespace, name = command_args[0].split('/', 1)
            async = len(command_args) > 1 and command_args[1] == '--async'
            return namespace, name, async
        except Exception:
            raise UsageError()

    def execute_async(self, namespace, name):
        return self._client.plugins.uninstall(namespace, name)


if __name__ == '__main__':
    main()
