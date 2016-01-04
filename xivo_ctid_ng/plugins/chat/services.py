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
from xivo_bus.resources.chat.event import ChatMessageEvent

logger = logging.getLogger(__name__)


class ChatService(AuthResource):

    def __init__(self, bus, config):
        self.bus = bus
        self.config = config

    def send(self, request):
        user_from = self.config.get('uuid'), request.get('from')
        to = self.config.get('uuid'), request.get('to')
        msg = request.get('msg')
        alias = request.get('alias')

        bus_event = ChatMessageEvent(user_from, to, alias, msg)
        self.bus.publish(bus_event)
