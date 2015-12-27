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


def not_found(error):
    return error.response is not None and error.response.status_code == 404


class IncomingRoomCallsService(object):

    def __init__(self, ari_config, ari):
        self._ari_config = ari_config
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

        return [{ 'data': [call.to_dict() for call in calls] }]

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

