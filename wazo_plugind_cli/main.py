# Copyright 2017-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import argparse
import logging
import sys

from cliff.app import App
from cliff.command import Command
from cliff.commandmanager import CommandManager
from wazo_auth_client import Client as AuthClient
from wazo_plugind_client import Client as PlugindClient

from . import config

logging.getLogger('requests').setLevel(logging.ERROR)


class WazoPlugindCLI(App):
    DEFAULT_VERBOSE_LEVEL = 0

    def __init__(self) -> None:
        super().__init__(
            description='A CLI for the wazo-plugind service',
            command_manager=CommandManager('wazo_plugind_cli.commands'),
            version='0.1',
        )
        self._current_token: str | None = None
        self._remove_token: bool = False
        self._client: PlugindClient | None = None
        self._auth_client: AuthClient | None = None
        self._config: dict | None = None

    def build_option_parser(self, *args: str, **kwargs: str) -> argparse.ArgumentParser:
        parser = super().build_option_parser(*args, **kwargs)
        parser.add_argument('--host', help='Hostname of the wazo-plugind server')
        parser.add_argument('--port', type=int, help='Port of the wazo-plugind server')
        return parser

    @property
    def client(self) -> PlugindClient:
        if not self._client:
            self._client = PlugindClient(**self._plugind_config)

        if not self._current_token:
            auth_config = dict(self._auth_config)
            username = auth_config.pop('service_id')
            password = auth_config.pop('service_key')
            auth_config.pop('key_file', None)
            self._auth_client = AuthClient(
                username=username, password=password, **auth_config
            )
            token_data = self._auth_client.token.new(expiration=3600)
            self._current_token = token_data['token']
            self._remove_token = True

        self._client.set_token(self._current_token)
        return self._client

    def initialize_app(self, argv: list[str]) -> None:
        self.LOG.debug('Wazo Plugind CLI')
        self.LOG.debug('options=%s', self.options)
        conf = config.build(self.options)
        self.LOG.debug('Starting with config: %s', conf)
        self._config = conf
        self._auth_config = dict(conf['auth'])
        self._plugind_config = dict(conf['plugind'])

    def clean_up(self, cmd: Command, result: int | None, err: Exception | None) -> None:
        if err:
            self.LOG.debug('got an error: %s', err)

        if self._remove_token and self._auth_client:
            self._auth_client.token.revoke(self._current_token)
            self._current_token = None
            self._remove_token = False


def _expand_deprecated_command_flag(argv: list[str]) -> list[str]:
    """Support legacy -c/--command flag by expanding its value into argv.

    e.g. ['-c', 'install git URL'] -> ['install', 'git', 'URL']
    """
    argv = list(argv)
    for i, arg in enumerate(argv):
        for flag in ('-c', '--command'):
            if arg == flag and i + 1 < len(argv):
                command_str = argv[i + 1]
                argv[i : i + 2] = command_str.split()
            elif arg.startswith(f'{flag}='):
                command_str = arg[len(flag) + 1 :]
                argv[i : i + 1] = command_str.split()
            else:
                continue
            print(
                f'Warning: {flag} is deprecated, use: wazo-plugind-cli {command_str}',
                file=sys.stderr,
            )
            return argv
    return argv


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    app = WazoPlugindCLI()
    return app.run(_expand_deprecated_command_flag(argv))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
