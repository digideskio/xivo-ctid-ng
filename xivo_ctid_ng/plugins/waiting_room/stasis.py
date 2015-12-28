# -*- coding: utf-8 -*-
# Copyright 2015 by Avencall
# SPDX-License-Identifier: GPL-3.0+

import logging

from xivo_bus.resources.calls.event import LeaveCallWaitingRoomEvent
from xivo_bus.resources.calls.event import UpdateWaitingRoomEvent
from xivo_bus.resources.calls.event import JoinCallWaitingRoomEvent 

logger = logging.getLogger(__name__)


class WaitingRoomCallsStasis(object):

    def __init__(self, ari_client, bus, services):
        self.ari = ari_client
        self.bus = bus
        self.services = services

    def subscribe(self):
        self.ari.on_channel_event('ChannelEnteredBridge', self.join_waiting_room)
        self.ari.on_channel_event('ChannelLeftBridge', self.leave_waiting_room)

    def join_waiting_room(self, channel, event):
        waiting_room_id = event.get('bridge').get('name')
        if 'hold' not in waiting_room_id:
            return
        bridge_id = self.ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
        bridge_real_id = event.get('bridge').get('id')

        if bridge_id == bridge_real_id:
            call = self.services.make_call_from_channel(self.ari, channel)
            bus_event = JoinCallWaitingRoomEvent(call.to_dict())
            self.bus.publish(bus_event)

    def leave_waiting_room(self, channel, event):
        waiting_room_id = event.get('bridge').get('name')
        if 'hold' not in waiting_room_id:
            return
        bridge_id = self.ari.asterisk.getGlobalVar(variable=waiting_room_id).get('value', None)
        bridge_real_id = event.get('bridge').get('id')

        if bridge_id == bridge_real_id:
            call = self.services.make_call_from_channel(self.ari, channel)
            bus_event = LeaveCallWaitingRoomEvent(call.to_dict())
            self.bus.publish(bus_event)

