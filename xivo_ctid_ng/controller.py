# -*- coding: utf-8 -*-
#
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

import logging

from multiprocessing import Process
from multiprocessing import Queue
from xivo_ctid_ng.core.rest_api import CoreRestApi
from xivo_ctid_ng.core.bus import CoreBus
from xivo_ctid_ng.core.call_control import CoreCallControl

logger = logging.getLogger(__name__)


class Controller(object):
    def __init__(self, config):
        self.config = config
        subscribeMsgQueue = Queue()
        self.rest_api = CoreRestApi(self.config['rest_api'])
        self.rest_api.app.config['ari'] = self.config['ari']
        self.rest_api.app.config['confd'] = self.config['confd']
        self.rest_api.app.config['auth'] = self.config['auth']
        self.bus = CoreBus(self.config['bus'])
        self.callcontrol = CoreCallControl(self.config['ari'], subscribeMsgQueue)

    def run(self):
        logger.debug('xivo-ctid-ng running...')
        bus_process = Process(target=self.bus.run, name='bus_process')
        bus_process.start()
        cc_process = Process(target=self.callcontrol.run, name='callcontrol_process')
        cc_process.start()
        self.rest_api.run()
