# Copyright 2017-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from collections.abc import Mapping
from queue import Queue
from threading import Thread
from typing import Any

from kombu import Connection, Exchange
from kombu import Queue as AMQPQueue
from kombu.mixins import ConsumerMixin


class ProgressConsumer(ConsumerMixin):
    def __init__(self, config: Mapping[str, Any]) -> None:
        if 'bus' in config:
            config = config['bus']

        url = 'amqp://{username}:{password}@{host}:{port}//'.format(**config)
        self.connection = Connection(url)
        self._exchange = Exchange(config['exchange_name'], config['exchange_type'])
        self._thread: Thread | None = None
        self._messages: Queue | None = None

    def __enter__(self) -> ProgressConsumer:
        if self.is_running:
            raise RuntimeError('thread is already running')

        self._messages = Queue()
        self._thread = Thread(target=self.run)
        self._thread.start()
        return self

    def __exit__(self, *args: Any) -> None:
        if not self.is_running or self._thread is None:
            raise RuntimeError('thread is not running')
        self.should_stop = True
        self._thread.join()

    def __iter__(self) -> ProgressConsumer:
        return self

    def __next__(self) -> dict:
        if not self.is_running or self._messages is None:
            raise RuntimeError('thread is not running')
        return self._messages.get()

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def get_consumers(self, Consumer: Any, channel: Any) -> list:
        def callback(body: dict, message: Any) -> None:
            if self._messages is not None:
                self._messages.put_nowait(body)
            message.ack()

        return [
            Consumer(
                AMQPQueue(
                    exchange=self._exchange,
                    auto_delete=True,
                    exclusive=True,
                ),
                callbacks=[callback],
            )
        ]
