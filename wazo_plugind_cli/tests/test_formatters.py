# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import io

from wazo_plugind_cli.formatters import LegacyPluginListFormatter


class TestLegacyPluginListFormatter:
    def test_empty_list(self) -> None:
        stdout = io.StringIO()
        formatter = LegacyPluginListFormatter()
        formatter.emit_list(('namespace', 'name', 'version'), [], stdout, None)
        assert stdout.getvalue() == '* List of plugins installed *\n'

    def test_renders_rows(self) -> None:
        stdout = io.StringIO()
        formatter = LegacyPluginListFormatter()
        formatter.emit_list(
            ('namespace', 'name', 'version'),
            [
                ('official', 'foo', '1.0'),
                ('official', 'bar', '2.1'),
            ],
            stdout,
            None,
        )
        assert stdout.getvalue() == (
            '* List of plugins installed *\n'
            '- official/foo (1.0)\n'
            '- official/bar (2.1)\n'
        )
