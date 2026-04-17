# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from cliff.formatters.base import ListFormatter


class LegacyPluginListFormatter(ListFormatter):
    def add_argument_group(self, parser):
        pass

    def add_rows(self, data):
        self._rows = data

    def emit_list(self, column_names, data, stdout, parsed_args):
        indices = {name: i for i, name in enumerate(column_names)}
        stdout.write('* List of plugins installed *\n')
        for row in data:
            row = tuple(row)
            namespace = row[indices['namespace']]
            name = row[indices['name']]
            version = row[indices['version']]
            stdout.write(f'- {namespace}/{name} ({version})\n')
