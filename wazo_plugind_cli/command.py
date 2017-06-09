# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import queue
import threading
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

    _end_status = ['completed', 'error']

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
        msg_queue = queue.Queue()
        status = None
        last_status = None
        with kombu.Connection(self.amqp_url) as conn:
            consumer = ProgressConsumer(conn, self.routing_key, self.exchange, msg_queue)
            thread = threading.Thread(target=consumer.run)
            thread.start()
            try:
                result = self.execute_async(*args)
                command_uuid = result['uuid']
                last_status = self._wait_for_progress(msg_queue, command_uuid)
            finally:
                consumer.should_stop = True
                thread.join()
                if last_status and last_status['status'] == 'error':
                    raise Exception(last_status)

    def _wait_for_progress(self, msg_queue, command_uuid):
        while True:
            msg = msg_queue.get()
            if msg['data']['uuid'] != command_uuid:
                continue

            status = msg['data']['status']
            done = status in self._end_status
            end = '\n' if done else '...\n'
            print('{}'.format(status), end=end)
            if done:
                return msg['data']


class InstallCommand(_BaseAsyncCommand):

    help = 'Install a plugin'
    usage = '<method> <plugin> [--async]'
    routing_key = 'plugin.install.*.*'

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
    routing_key = 'plugin.uninstall.*.*'

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
            print('- {namespace}/{name} ({version})'.format(**result))

