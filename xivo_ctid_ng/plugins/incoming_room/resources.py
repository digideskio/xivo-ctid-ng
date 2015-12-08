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

import ari
import logging
import requests

from flask import current_app
from flask import request
from contextlib import contextmanager

from dateutil import tz
from datetime import datetime

from xivo_ctid_ng.core.rest_api import AuthResource

from .exceptions import AsteriskARIUnreachable

logger = logging.getLogger(__name__)


@contextmanager
def new_ari_client(config):
    try:
        yield ari.connect(**config)
    except requests.ConnectionError as e:
        raise AsteriskARIUnreachable(config, e)


class IncomingRoomCallsResource(AuthResource):

    def get(self, incoming_room_id):
        with new_ari_client(current_app.config['ari']['connection']) as ari:
            bridge_id = ari.asterisk.getGlobalVar(variable=incoming_room_id).get('value', None)
            bridge = ari.bridges.get(bridgeId=bridge_id)
            channels = bridge.json.get('channels', None)
            return {'channels': channels}, 201

class IncomingRoomCallsAssociationResource(AuthResource):

    def put(self, incoming_room_id, call_id):
        with new_ari_client(current_app.config['ari']['connection']) as ari:
            bridge_id = ari.asterisk.getGlobalVar(variable=incoming_room_id).get('value', None)
            bridge = ari.bridges.get(bridgeId=bridge_id)
            channel = ari.channels.get(channelId=call_id)
            channel.answer()
            channel.setChannelVar(variable='bridgeentertime',value=datetime.now(tz.tzlocal()).isoformat())
            bridge.addChannel(channel=call_id)

            return {'bridge_id': bridge.id}, 201
