# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import kombu

from xivo.cli import BaseCommand, UsageError
from .bus import ProgressConsumer


class _BasePlugindCommand(BaseCommand):

    def __init__(self, client):
        super().__init__()
        self._client = client

    def execute(self):
        raise NotImplementedError()


class _BaseAsyncCommand(_BasePlugindCommand):

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


class InstallCommand(_BaseAsyncCommand):

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


class UninstallCommand(_BaseAsyncCommand):

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


class ListCommand(_BasePlugindCommand):

    help = 'List plugins'

    def execute(self):
        results = self._client.plugins.list()
        print('* List of plugins installed *')
        for result in results['items']:
            print('- {name} ({version})'.format(**result))

