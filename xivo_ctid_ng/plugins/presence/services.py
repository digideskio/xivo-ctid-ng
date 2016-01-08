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

import logging

from xivo_ctid_ng.core.rest_api import AuthResource
from xivo_bus.resources.cti.event import UserStatusUpdateEvent

logger = logging.getLogger(__name__)


class PresenceService(AuthResource):

    def __init__(self, bus, config):
        self.bus = bus
        self.config = config

    def send(self, request):
        user_id = request.get('user_id')
        status_name = request.get('status_name')

        bus_event = UserStatusUpdateEvent(user_id, status_name)
        self.bus.publish(bus_event)
