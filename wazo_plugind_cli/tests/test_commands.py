# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from argparse import Namespace
from unittest.mock import MagicMock, Mock, patch

import pytest

from wazo_plugind_cli.commands import (
    InstallCommand,
    ListCommand,
    UninstallCommand,
    _is_valid_message,
    _wait_for_progress,
)


class TestIsValidMessage:
    def test_matching_uuid(self) -> None:
        message = {'data': {'uuid': 'abc'}}
        assert _is_valid_message(message, 'abc') is True

    def test_mismatched_uuid(self) -> None:
        message = {'data': {'uuid': 'abc'}}
        assert _is_valid_message(message, 'xyz') is False

    def test_missing_data(self) -> None:
        assert _is_valid_message({}, 'abc') is False

    def test_missing_uuid(self) -> None:
        assert _is_valid_message({'data': {}}, 'abc') is False


class TestWaitForProgress:
    def test_filters_by_uuid_and_stops_on_completed(self) -> None:
        consumer = iter(
            [
                {'data': {'uuid': 'other', 'status': 'building'}},
                {'data': {'uuid': 'abc', 'status': 'building'}},
                {'data': {'uuid': 'abc', 'status': 'completed'}},
            ]
        )
        result = _wait_for_progress(consumer, 'abc')
        assert result == {'uuid': 'abc', 'status': 'completed'}

    def test_stops_on_error(self) -> None:
        consumer = iter(
            [
                {'data': {'uuid': 'abc', 'status': 'error'}},
            ]
        )
        result = _wait_for_progress(consumer, 'abc')
        assert result == {'uuid': 'abc', 'status': 'error'}


class TestInstallCommand:
    def _make_app(self) -> Mock:
        app = Mock()
        app._config = {'bus': {}}
        return app

    def test_async_does_not_stream(self) -> None:
        app = self._make_app()
        app.client.plugins.install.return_value = {'uuid': 'abc'}
        cmd = InstallCommand(app, None)
        parsed_args = Namespace(
            method='git',
            plugin='https://example.org/repo.git',
            ref=None,
            subdirectory=None,
            async_=True,
        )
        cmd.take_action(parsed_args)
        app.client.plugins.install.assert_called_once_with(
            'https://example.org/repo.git', 'git', {}
        )

    def test_git_with_ref_and_subdirectory(self) -> None:
        app = self._make_app()
        app.client.plugins.install.return_value = {'uuid': 'abc'}
        cmd = InstallCommand(app, None)
        parsed_args = Namespace(
            method='git',
            plugin='https://example.org/repo.git',
            ref='main',
            subdirectory='subdir',
            async_=True,
        )
        cmd.take_action(parsed_args)
        app.client.plugins.install.assert_called_once_with(
            'https://example.org/repo.git',
            'git',
            {'ref': 'main', 'subdirectory': 'subdir'},
        )

    def test_non_git_ignores_ref(self) -> None:
        app = self._make_app()
        app.client.plugins.install.return_value = {'uuid': 'abc'}
        cmd = InstallCommand(app, None)
        parsed_args = Namespace(
            method='market',
            plugin='official/some-plugin',
            ref='main',
            subdirectory=None,
            async_=True,
        )
        cmd.take_action(parsed_args)
        app.client.plugins.install.assert_called_once_with(
            'official/some-plugin', 'market', {}
        )

    @patch('wazo_plugind_cli.commands.ProgressConsumer')
    def test_sync_streams_progress(self, mock_consumer_cls: Mock) -> None:
        app = self._make_app()
        app.client.plugins.install.return_value = {'uuid': 'abc'}

        consumer = MagicMock()
        consumer.__iter__.return_value = iter(
            [{'data': {'uuid': 'abc', 'status': 'completed'}}]
        )
        mock_consumer_cls.return_value.__enter__.return_value = consumer

        cmd = InstallCommand(app, None)
        parsed_args = Namespace(
            method='git',
            plugin='https://example.org/repo.git',
            ref=None,
            subdirectory=None,
            async_=False,
        )
        cmd.take_action(parsed_args)
        mock_consumer_cls.assert_called_once_with(app._config)


class TestUninstallCommand:
    def _make_app(self) -> Mock:
        app = Mock()
        app._config = {'bus': {}}
        return app

    def test_async(self) -> None:
        app = self._make_app()
        app.client.plugins.uninstall.return_value = {'uuid': 'abc'}
        cmd = UninstallCommand(app, None)
        parsed_args = Namespace(plugin='official/admin-ui-conference', async_=True)
        cmd.take_action(parsed_args)
        app.client.plugins.uninstall.assert_called_once_with(
            'official', 'admin-ui-conference'
        )

    def test_invalid_plugin_raises(self) -> None:
        app = self._make_app()
        cmd = UninstallCommand(app, None)
        parsed_args = Namespace(plugin='no-slash', async_=True)
        with pytest.raises(ValueError):
            cmd.take_action(parsed_args)


class TestListCommand:
    def test_take_action_returns_columns_and_rows(self) -> None:
        app = Mock()
        app.client.plugins.list.return_value = {
            'items': [
                {'namespace': 'official', 'name': 'foo', 'version': '1.0'},
                {'namespace': 'official', 'name': 'bar', 'version': '2.1'},
            ]
        }
        cmd = ListCommand(app, None)
        columns, rows = cmd.take_action(Namespace())
        assert columns == ('namespace', 'name', 'version')
        assert rows == [
            ('official', 'foo', '1.0'),
            ('official', 'bar', '2.1'),
        ]
