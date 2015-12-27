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
import requests

from dateutil import tz
from datetime import datetime

from .call import Call

logger = logging.getLogger(__name__)


class IncomingRoomCallsService(object):

    def __init__(self, ari_config, confd_config, ari):
        self._ari_config = ari_config
        self._confd_config = confd_config
        self._ari = ari

    def list_calls(self, incoming_room_id):
        ari = self._ari.client
        calls = []

        bridge_id = ari.asterisk.getGlobalVar(variable=incoming_room_id).get('value', None)
        try:
            bridge = ari.bridges.get(bridgeId=bridge_id)
        except requests.HTTPError:
            return {'message': 'There is no incoming bridge'}, 200

        channels = bridge.json.get('channels', None)

        for chan in channels:
            channel = ari.channels.get(channelId=chan)
            result_call = Call(channel.id, channel.json['creationtime'])
            result_call.status = channel.json['state']
            result_call.user_uuid = ""
            result_call.caller_id_number = channel.json['caller']['number']
            result_call.caller_id_name = channel.json['caller']['name']
            result_call.bridges = list()
            result_call.talking_to = dict()

            calls.append(result_call)

        return { 'items': [call.to_dict() for call in calls] }

    def add_call(self, incoming_room_id, call_id):
        ari = self._ari.client

        bridge_id = ari.asterisk.getGlobalVar(variable=incoming_room_id).get('value', None)
        bridge = ari.bridges.get(bridgeId=bridge_id)
        if len(bridge.json.get('channels')) < 1:
            bridge.startMoh()
        channel = ari.channels.get(channelId=call_id)
        channel.answer()
        channel.setChannelVar(variable='bridgeentertime',value=datetime.now(tz.tzlocal()).isoformat())
        bridge.addChannel(channel=call_id)

        return bridge.id
