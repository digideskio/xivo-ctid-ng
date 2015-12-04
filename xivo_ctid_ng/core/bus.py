# -*- coding: utf-8 -*-
# Copyright (C) 2015 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import json
import logging

from kombu import Connection
from kombu import Exchange
from kombu import Queue
from kombu.pools import producers

logger = logging.getLogger(__name__)


class CoreBus(object):

    def __init__(self, config, queue):
        super(CoreBus, self).__init__()
        self.config = config
        self.queue = queue
        self.publish = None

    def run(self):
        logger.info("Running AMQP interfaces publisher")
        self._publish()

    def stop(self):
        if self.publish:
           self.publish.should_stop = True

    def _publish(self):
        uri = 'amqp://{username}:{password}@{host}:{port}//'.format(**self.config)
        with producers[Connection(uri)].acquire(block=True) as conn:
            self.publish = Publisher(conn, self.queue)
            self.publish.init_app(self.config)
            self.publish.run()

class Publisher(object):
    def __init__(self, connection, queue):
        self.conn = connection
        self.queue = queue
        self.exchange = None
        self.routing_key = None
        self.type = None
        self.should_stop = False

    def init_app(self, config):
        self.exchange = config['exchange_name']
        self.type = config['exchange_type']
        self.routing_key = 'calls'

    def run(self):
        while not self.should_stop:
            message = self.queue.get(0.1)
            if message:
                print "Send message : ", message
                self.publish(message)

    def publish(self, data):
        self.conn.publish(data, exchange=self.exchange, routing_key=self.routing_key)
