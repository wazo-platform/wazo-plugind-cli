# Copyright 2017-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo.cli import BaseCommand, UsageError

from .bus import ProgressConsumer


class _BasePlugindCommand(BaseCommand):
    def __init__(self, client):
        super().__init__()
        self._client = client

    def execute(self):
        raise NotImplementedError()


class _BaseAsyncCommand(_BasePlugindCommand):
    _end_status = ['completed', 'error']

    def __init__(self, plugind_client, config):
        super().__init__(plugind_client)
        self._config = config

    def execute(self, *args):
        async_ = args[-1]
        if async_:
            self.execute_async(*args[:-1])
        else:
            self.execute_sync(*args[:-1])

    def execute_sync(self, *args):
        with ProgressConsumer(self._config) as consumer:
            result = self.execute_async(*args)
            command_uuid = result['uuid']
            last_status = self._wait_for_progress(consumer, command_uuid)

        if last_status and last_status['status'] == 'error':
            raise Exception(last_status)

    def _wait_for_progress(self, consumer, command_uuid):
        for message in consumer:
            if not self._is_valid_message(message, command_uuid):
                continue

            status = message['data']['status']
            done = status in self._end_status
            end = '\n' if done else '...\n'

            print(f'{status}', end=end)
            if done:
                return message['data']

    def _is_valid_message(self, message, expected_uuid):
        try:
            return message['data']['uuid'] == expected_uuid
        except KeyError:
            return False


class InstallCommand(_BaseAsyncCommand):
    help = 'Install a plugin'
    usage = '<method> <plugin> [--ref reference] [--async]'
    routing_key = 'plugin.install.*.*'

    def prepare(self, command_args):
        options = {}
        try:
            method = command_args[0]
            plugin = command_args[1]
            optional_args = command_args[2:]
            async_ = '--async' in optional_args
            if method == 'git':
                if '--ref' in optional_args:
                    value_index = optional_args.index('--ref') + 1
                    options['ref'] = optional_args[value_index]
                if '--subdirectory' in optional_args:
                    value_index = optional_args.index('--subdirectory') + 1
                    options['subdirectory'] = optional_args[value_index]
            return method, plugin, options, async_
        except Exception:
            raise UsageError()

    def execute_async(self, method, plugin, options):
        return self._client.plugins.install(plugin, method, options)


class UninstallCommand(_BaseAsyncCommand):
    help = 'Uninstall a plugin'
    usage = '<namespace>/<name> [--async]'
    routing_key = 'plugin.uninstall.*.*'

    def prepare(self, command_args):
        try:
            namespace, name = command_args[0].split('/', 1)
            async_ = len(command_args) > 1 and command_args[1] == '--async'
            return namespace, name, async_
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
            print('- {namespace}/{name} ({version})'.format(**result))
