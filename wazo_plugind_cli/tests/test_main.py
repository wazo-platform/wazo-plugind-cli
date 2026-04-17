# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import Mock, patch

from wazo_plugind_cli.main import WazoPlugindCLI, _expand_deprecated_command_flag


class TestClientProperty:
    def _make_app(self):
        with patch.object(WazoPlugindCLI, '__init__', lambda self: None):
            app = WazoPlugindCLI()
        app._current_token = None
        app._remove_token = False
        app._client = None
        app._auth_client = None
        app._plugind_config = {
            'host': 'localhost',
            'port': 9503,
        }
        app._auth_config = {
            'host': 'localhost',
            'port': 9497,
            'service_id': 'my-service',
            'service_key': 'my-secret',
            'key_file': '/some/path',
        }
        return app

    @patch('wazo_plugind_cli.main.AuthClient')
    @patch('wazo_plugind_cli.main.PlugindClient')
    def test_creates_token_lazily(self, mock_plugind, mock_auth):
        mock_auth.return_value.token.new.return_value = {'token': 'my-token'}
        app = self._make_app()

        client = app.client

        mock_auth.assert_called_once_with(
            username='my-service',
            password='my-secret',
            host='localhost',
            port=9497,
        )
        mock_auth.return_value.token.new.assert_called_once_with(expiration=3600)
        mock_plugind.assert_called_once_with(host='localhost', port=9503)
        client.set_token.assert_called_with('my-token')
        assert app._remove_token is True

    @patch('wazo_plugind_cli.main.AuthClient')
    @patch('wazo_plugind_cli.main.PlugindClient')
    def test_caches_on_second_access(self, mock_plugind, mock_auth):
        mock_auth.return_value.token.new.return_value = {'token': 'my-token'}
        app = self._make_app()

        app.client
        app.client

        mock_auth.return_value.token.new.assert_called_once()


class TestCleanUp:
    def test_revokes_token_when_created(self):
        app = Mock(spec=WazoPlugindCLI)
        app._remove_token = True
        app._current_token = 'my-token'
        app._auth_client = Mock()

        WazoPlugindCLI.clean_up(app, cmd=None, result=None, err=None)

        app._auth_client.token.revoke.assert_called_once_with('my-token')
        assert app._remove_token is False

    def test_does_nothing_when_no_token(self):
        app = Mock(spec=WazoPlugindCLI)
        app._remove_token = False
        app._auth_client = Mock()
        app.LOG = Mock()

        WazoPlugindCLI.clean_up(app, cmd=None, result=None, err=None)

        app._auth_client.token.revoke.assert_not_called()


class TestExpandDeprecatedCommandFlag:
    def test_short_flag(self):
        result = _expand_deprecated_command_flag(['-c', 'install git URL'])
        assert result == ['install', 'git', 'URL']

    def test_long_flag(self):
        result = _expand_deprecated_command_flag(['--command', 'list'])
        assert result == ['list']

    def test_short_flag_equals_form(self):
        result = _expand_deprecated_command_flag(['-c=list'])
        assert result == ['list']

    def test_long_flag_equals_form(self):
        result = _expand_deprecated_command_flag(['--command=install git URL'])
        assert result == ['install', 'git', 'URL']

    def test_flag_mixed_with_other_args(self):
        result = _expand_deprecated_command_flag(['--host', 'myhost', '-c', 'list'])
        assert result == ['--host', 'myhost', 'list']

    def test_flag_without_value(self):
        assert _expand_deprecated_command_flag(['-c']) == ['-c']

    def test_no_flag(self):
        assert _expand_deprecated_command_flag(['install', 'git', 'URL']) == [
            'install',
            'git',
            'URL',
        ]
