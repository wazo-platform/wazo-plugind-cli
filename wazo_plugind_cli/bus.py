# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import kombu
from kombu.mixins import ConsumerMixin


class ProgressConsumer(ConsumerMixin):

    _end_status = ['completed', 'error']

    def __init__(self, connection, routing_key, exchange):
        self.connection = connection
        self.routing_key = routing_key
        self._exchange = exchange

    def get_consumers(self, Consumer, channel):
        return [Consumer(kombu.Queue(exchange=self._exchange,
                                     routing_key=self.routing_key,
                                     exclusive=True),
                         callbacks=[self.on_message])]

    def on_message(self, body, message):
        status = body['data']['status']
        print(status)
        message.ack()
        if status in self._end_status:
            self.should_stop = True
