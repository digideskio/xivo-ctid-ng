# -*- coding: utf-8 -*-
# Copyright 2015 by Avencall
# SPDX-License-Identifier: GPL-3.0+

import logging

from xivo_bus.resources.calls.event import JoinCallIncomingRoomEvent 
from xivo_bus.resources.calls.event import LeaveCallIncomingRoomEvent

logger = logging.getLogger(__name__)


class IncomingRoomCallsStasis(object):

    def __init__(self, ari_client, bus, services):
        self.ari = ari_client
        self.bus = bus
        self.services = services

    def subscribe(self):
        pass
