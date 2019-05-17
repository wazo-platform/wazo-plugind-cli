# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import kombu
from kombu.mixins import ConsumerMixin


class ProgressConsumer(ConsumerMixin):

    def __init__(self, connection, routing_key, exchange, msg_queue):
        self.connection = connection
        self.routing_key = routing_key
        self._exchange = exchange
        self._msg_queue = msg_queue

    def get_consumers(self, Consumer, channel):
        return [Consumer(kombu.Queue(exchange=self._exchange,
                                     routing_key=self.routing_key,
                                     exclusive=True),
                         callbacks=[self._on_message])]

    def _on_message(self, body, message):
        self._msg_queue.put(body)
        message.ack()
