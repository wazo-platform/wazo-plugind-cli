# Copyright 2017-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Thread
from queue import Queue
from kombu.mixins import ConsumerMixin
from kombu import Exchange, Queue as AMQPQueue, Connection


class ProgressConsumer(ConsumerMixin):
    def __init__(self, config):
        if 'bus' in config:
            config = config['bus']

        url = 'amqp://{username}:{password}@{host}:{port}//'.format(**config)
        self.connection = Connection(url)
        self._exchange = Exchange(config['exchange_name'], config['exchange_type'])
        self._thread = None
        self._messages = None

    def __enter__(self):
        if self.is_running:
            raise RuntimeError('thread is already running')

        self._messages = Queue()
        self._thread = Thread(target=self.run)
        self._thread.start()
        return self

    def __exit__(self, *args):
        if not self.is_running:
            raise RuntimeError('thread is not running')
        self.should_stop = True
        self._thread.join()

    def __iter__(self):
        return self

    def __next__(self):
        if not self.is_running:
            raise RuntimeError('thread is not running')
        return self._messages.get()

    @property
    def is_running(self):
        return self._thread and self._thread.is_alive()

    def get_consumers(self, Consumer, channel):
        def callback(body, message):
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
