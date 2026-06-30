# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from typing import Any, TextIO

from cliff.formatters.base import ListFormatter


class LegacyPluginListFormatter(ListFormatter):
    def add_argument_group(self, parser: argparse.ArgumentParser) -> None:
        pass

    def add_rows(self, data: Iterable[Sequence[Any]]) -> None:
        self._rows = data

    def emit_list(
        self,
        column_names: Sequence[str],
        data: Iterable[Sequence[Any]],
        stdout: TextIO,
        parsed_args: argparse.Namespace | None,
    ) -> None:
        indices = {name: i for i, name in enumerate(column_names)}
        stdout.write('* List of plugins installed *\n')
        for row in data:
            row = tuple(row)
            namespace = row[indices['namespace']]
            name = row[indices['name']]
            version = row[indices['version']]
            stdout.write(f'- {namespace}/{name} ({version})\n')
