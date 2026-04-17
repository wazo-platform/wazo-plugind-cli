#!/usr/bin/env python3
# Copyright 2017-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import find_packages, setup

setup(
    name='wazo-plugind-cli',
    version='0.1',
    author='Wazo Authors',
    author_email='dev@wazo.community',
    url='http://wazo.community',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'wazo-plugind-cli = wazo_plugind_cli.main:main',
        ],
        'wazo_plugind_cli.commands': [
            'install = wazo_plugind_cli.commands:InstallCommand',
            'uninstall = wazo_plugind_cli.commands:UninstallCommand',
            'list = wazo_plugind_cli.commands:ListCommand',
        ],
    },
)
