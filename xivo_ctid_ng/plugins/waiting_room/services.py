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

from xivo_ctid_ng.core.rest_api import AuthResource

from .call import Call

from xivo_bus.resources.calls.event import CreateWaitingRoomEvent
from xivo_bus.resources.calls.event import DeleteWaitingRoomEvent

logger = logging.getLogger(__name__)


def not_found(error):
    return error.response is not None and error.response.status_code == 404


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

        return { 'data': [call.to_dict() for call in calls] }

    def add_call(self, waiting_room_id, call_id):
        ari = self._ari.client

        bridge_id = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
        bridge = ari.bridges.get(bridgeId=bridge_id)
        channel = ari.channels.get(channelId=call_id)
        channel.answer()
        channel.setChannelVar(variable='bridgeentertime',value=datetime.now(tz.tzlocal()).isoformat())
        bridge.addChannel(channel=call_id)

        return bridge.id

    def create_waiting_room(self, waiting_room_id, request):
        ari = self._ari.client

        moh_hold = request.get('moh', None)

        hold_bridge = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
        if hold_bridge:
            return {'message': 'Bridge already exist'}, 200

        bridge = ari.bridges.create(type='holding', name=waiting_room_id)
        ari.asterisk.setGlobalVar(variable=waiting_room_id, value=bridge.id)
        if moh_hold:
            bridge.startMoh(mohClass=moh_hold)

        event = {'bridge_id': bridge.id,
                 'waiting_room_id': waiting_room_id
                }
        bus_event = CreateWaitingRoomEvent(event)
        self.bus.publish(bus_event)

        return bridge.id

    def delete_call_from_waiting_room(self, waiting_room_id):
        ari = self._ari.client

        bridge_id = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
        ari.asterisk.setGlobalVar(variable=waiting_room_id, value='')
        bridge = ari.bridges.destroy(bridgeId=bridge_id)

        event = {'waiting_room_id': waiting_room_id,
                 'bridge_id': bridge_id
                }
        bus_event = DeleteWaitingRoomEvent(event)
        self.bus.publish(bus_event)

    def make_call_from_channel(self, ari, channel):
        call = Call(channel.id, channel.json['creationtime'])
        call.status = channel.json['state']
        call.caller_id_name = channel.json['caller']['name']
        call.caller_id_number = channel.json['caller']['number']
        call.user_uuid = self._get_uuid_from_channel_id(ari, channel.id)
        call.bridges = [bridge.id for bridge in ari.bridges.list() if channel.id in bridge.json['channels']]

        call.talking_to = dict()
        for channel_id in self._get_channel_ids_from_bridges(ari, call.bridges):
            talking_to_user_uuid = self._get_uuid_from_channel_id(ari, channel_id)
            call.talking_to[channel_id] = talking_to_user_uuid
        call.talking_to.pop(channel.id, None)

        return call

    def _get_uuid_from_channel_id(self, ari, channel_id):
        try:
            return ari.channels.getChannelVar(channelId=channel_id, variable='XIVO_USERUUID')['value']
        except requests.HTTPError as e:
            if not_found(e):
                return None
            raise

        return None

    def _get_channel_ids_from_bridges(self, ari, bridges):
        result = set()
        for bridge_id in bridges:
            try:
                channels = ari.bridges.get(bridgeId=bridge_id).json['channels']
            except requests.RequestException as e:
                logger.error(e)
                channels = set()
            result.update(channels)
        return result

