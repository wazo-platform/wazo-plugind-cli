# Copyright 2017-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from argparse import Namespace
from typing import Any

from xivo.chain_map import ChainMap
from xivo.config_helper import parse_config_file

_DEFAULT_CONFIG = {
    'auth': {
        'host': 'localhost',
        'port': 80,
        'https': False,
        'key_file': '/var/lib/wazo-auth-keys/wazo-plugind-cli-key.yml',
    },
    'plugind': {
        'host': 'localhost',
        'port': 9503,
        'prefix': None,
        'https': False,
    },
    'bus': {
        'username': 'guest',
        'password': 'guest',
        'host': 'localhost',
        'port': 5672,
        'exchange_name': 'wazo-headers',
        'exchange_type': 'headers',
    },
}


def _args_to_dict(parsed_args: Namespace) -> dict[str, Any]:
    plugind_config: dict[str, Any] = {}
    host = getattr(parsed_args, 'host', None)
    if host:
        plugind_config['host'] = host
    port = getattr(parsed_args, 'port', None)
    if port:
        plugind_config['port'] = port

    config: dict[str, Any] = {}
    if plugind_config:
        config['plugind'] = plugind_config

    return config


def _load_key_file(config: ChainMap) -> dict[str, dict[str, str]]:
    key_file = parse_config_file(config['auth']['key_file'])
    return {
        'auth': {
            'service_id': key_file['service_id'],
            'service_key': key_file['service_key'],
        }
    }


def build(parsed_args: Namespace) -> ChainMap:
    cli_config = _args_to_dict(parsed_args)
    key_config = _load_key_file(ChainMap(cli_config, _DEFAULT_CONFIG))
    return ChainMap(cli_config, key_config, _DEFAULT_CONFIG)
