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


class WaitingRoomCallsResource(AuthResource):

    def get(self, waiting_room_id):

        calls = []
        with new_ari_client(current_app.config['ari']['connection']) as ari:
            bridge_id = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
            bridge = ari.bridges.get(bridgeId=bridge_id)
            channels = bridge.json.get('channels', None)

            for chan in channels:
                channel = ari.channels.get(channelId=chan)
                result_call = Call(channel.id, channel.json['creationtime'])
                result_call.status = channel.json['state']
                result_call.user_uuid = ""
                result_call.bridges = list()
                result_call.talking_to = dict()

                calls.append(result_call)

            return {
                'items': [call.to_dict() for call in calls],
            }, 201

class WaitingRoomCallsAssociationResource(AuthResource):

    def put(self, waiting_room_id, call_id):
        with new_ari_client(current_app.config['ari']['connection']) as ari:
            bridge_id = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
            bridge = ari.bridges.get(bridgeId=bridge_id)
            channel = ari.channels.get(channelId=call_id)
            channel.answer()
            channel.setChannelVar(variable='bridgeentertime',value=datetime.now(tz.tzlocal()).isoformat())
            bridge.addChannel(channel=call_id)

            return {'bridge_id': bridge.id}, 201

class WaitingRoomResource(AuthResource):

    def post(self, waiting_room_id):
        moh_hold = request.json.get('moh', None)

        with new_ari_client(current_app.config['ari']['connection']) as ari:
            hold_bridge = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
            if hold_bridge:
                return {'message': 'Bridge already exist'}, 200

            bridge = ari.bridges.create(type='holding')
            ari.asterisk.setGlobalVar(variable=waiting_room_id, value=bridge.id)
            if moh_hold:
                bridge.startMoh(mohClass=moh_hold)

            return {'bridge_id': bridge.id}, 201

    def delete(self, waiting_room_id, call_id):
        with new_ari_client(current_app.config['ari']['connection']) as ari:
            bridge_id = ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
            bridge = ari.bridges.get(bridgeID=bridge_id)
            bridge.removeChannel(call_id)

class Call(object):

    def __init__(self, id_, creation_time):
        self.id_ = id_
        self.creation_time = creation_time
        self.bridges = []
        self.status = 'Down'
        self.talking_to = []
        self.user_uuid = None

    def to_dict(self):
        return {
            'bridges': self.bridges,
            'call_id': self.id_,
            'creation_time': self.creation_time,
            'status': self.status,
            'talking_to': self.talking_to,
            'user_uuid': self.user_uuid,
        }

