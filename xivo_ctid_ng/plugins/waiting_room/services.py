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

from dateutil import tz
from datetime import datetime

from xivo_ctid_ng.core.rest_api import AuthResource

from .call import Call

from xivo_bus.resources.calls.event import CreateWaitingRoomEvent
from xivo_bus.resources.calls.event import DeleteWaitingRoomEvent

logger = logging.getLogger(__name__)


class WaitingRoomCallsService(AuthResource):

    def __init__(self, ari_config, ari, bus):
        self._ari_config = ari_config
        self._ari = ari
        self.bus = bus

    def list_calls(self, waiting_room_id):
        ari = self._ari.client

        calls = []
        bridge_id = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
        bridge = ari.bridges.get(bridgeId=bridge_id)
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

    def add_call(self, waiting_room_id, call_id):
        ari = self._ari.client

        bridge_id = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
        bridge = ari.bridges.get(bridgeId=bridge_id)
        channel = ari.channels.get(channelId=call_id)
        channel.answer()
        channel.setChannelVar(variable='bridgeentertime',value=datetime.now(tz.tzlocal()).isoformat())
        bridge.addChannel(channel=call_id)

        return bridge.id

    def create_waiting_room(self, waiting_room_id):
        ari = self._ari.client

        moh_hold = request.json.get('moh', None)

        hold_bridge = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
        if hold_bridge:
            return {'message': 'Bridge already exist'}, 200

        bridge = ari.bridges.create(type='holding')
        ari.asterisk.setGlobalVar(variable=waiting_room_id, value=bridge.id)
        if moh_hold:
            bridge.startMoh(mohClass=moh_hold)

        event = {'bridge_id': bridge_id,
                 'waiting_room_id': waiting_room_id
                }
        bus_event = CreateWaitingRoomEvent(event)
        self.bus.publish(bus_event)

        return bridge.id

    def delete_call_from_waiting_room(self, waiting_room_id, call_id):
        ari = self._ari.client

        bridge_id = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
        bridge = ari.bridges.get(bridgeID=bridge_id)
        bridge.removeChannel(call_id)

        event = {'waiting_room_id': waiting_room_id,
                 'call_id': call_id
                }
        bus_event = DeleteWaitingRoomEvent(event)
        self.bus.publish(bus_event)
