# Copyright 2017-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import argparse
from collections.abc import Iterator
from typing import Any

from cliff.command import Command
from cliff.lister import Lister

from .bus import ProgressConsumer

_END_STATUSES = ('completed', 'error')


def _is_valid_message(message: dict, expected_uuid: str) -> bool:
    try:
        return message['data']['uuid'] == expected_uuid
    except KeyError:
        return False


def _stream_progress_until_done(
    consumer: Iterator[dict], command_uuid: str
) -> dict | None:
    for message in consumer:
        if not _is_valid_message(message, command_uuid):
            continue

        status = message['data']['status']
        done = status in _END_STATUSES
        end = '\n' if done else '...\n'

        print(f'{status}', end=end)
        if done:
            return message['data']
    return None


def _wait_for_completion(consumer: Iterator[dict], command_uuid: str) -> None:
    last_status = _stream_progress_until_done(consumer, command_uuid)
    if last_status and last_status['status'] == 'error':
        raise Exception(last_status)


class InstallCommand(Command):
    """Install a plugin"""

    def get_parser(self, *args: Any, **kwargs: Any) -> argparse.ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('method', help='Installation method (e.g. git)')
        parser.add_argument('plugin', help='Plugin identifier (e.g. git URL)')
        parser.add_argument('--ref', help='Git reference (branch/tag/commit)')
        parser.add_argument('--subdirectory', help='Subdirectory within the repo')
        parser.add_argument(
            '--async',
            dest='async_',
            action='store_true',
            help='Do not wait for completion',
        )
        return parser

    def take_action(self, parsed_args: argparse.Namespace) -> None:
        options: dict[str, str] = {}
        if parsed_args.method == 'git':
            if parsed_args.ref:
                options['ref'] = parsed_args.ref
            if parsed_args.subdirectory:
                options['subdirectory'] = parsed_args.subdirectory

        if parsed_args.async_:
            self.app.client.plugins.install(
                parsed_args.plugin, parsed_args.method, options
            )
            return

        with ProgressConsumer(self.app._config) as consumer:
            result = self.app.client.plugins.install(
                parsed_args.plugin, parsed_args.method, options
            )
            _wait_for_completion(consumer, result['uuid'])


class UninstallCommand(Command):
    """Uninstall a plugin"""

    def get_parser(self, *args: Any, **kwargs: Any) -> argparse.ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('plugin', help='Plugin in the form <namespace>/<name>')
        parser.add_argument(
            '--async',
            dest='async_',
            action='store_true',
            help='Do not wait for completion',
        )
        return parser

    def take_action(self, parsed_args: argparse.Namespace) -> None:
        if '/' not in parsed_args.plugin:
            raise ValueError('plugin must be in the form <namespace>/<name>')
        namespace, name = parsed_args.plugin.split('/', 1)

        if parsed_args.async_:
            self.app.client.plugins.uninstall(namespace, name)
            return

        with ProgressConsumer(self.app._config) as consumer:
            result = self.app.client.plugins.uninstall(namespace, name)
            _wait_for_completion(consumer, result['uuid'])


class ListCommand(Lister):
    """List installed plugins"""

    COLUMNS = ('namespace', 'name', 'version')

    @property
    def formatter_default(self) -> str:
        return 'plugind_legacy'

    def take_action(
        self, parsed_args: argparse.Namespace
    ) -> tuple[tuple[str, ...], list[tuple[str, str, str]]]:
        results = self.app.client.plugins.list()
        rows = [
            (item['namespace'], item['name'], item['version'])
            for item in results['items']
        ]
        return self.COLUMNS, rows
