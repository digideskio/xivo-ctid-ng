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
        self.ari.on_channel_event('StasisStart', self.join_call_incoming_room)
        self.ari.on_channel_event('ChannelEnteredBridge', self.join_incoming_room)
        self.ari.on_channel_event('ChannelLeftBridge', self.leave_incoming_room)

    def leave_incoming_room(self, channel, event):
        incoming_room_id = event.get('bridge').get('name')
        if 'hold' in incoming_room_id:
            return
        bridge_id = self.ari.asterisk.getGlobalVar(variable=incoming_room_id).get('value', None)
        bridge_real_id = event.get('bridge').get('id')

        if bridge_id == bridge_real_id:
            call = self.services.make_call_from_channel(self.ari, channel)
            bus_event = LeaveCallIncomingRoomEvent(call.to_dict())
            self.bus.publish(bus_event)

    def join_incoming_room(self, channel, event):
        incoming_room_id = event.get('bridge').get('name')
        if 'hold' in incoming_room_id:
            return
        bridge_id = self.ari.asterisk.getGlobalVar(variable=incoming_room_id).get('value', None)
        bridge_real_id = event.get('bridge').get('id')

        if bridge_id == bridge_real_id:
            call = self.services.make_call_from_channel(self.ari, channel)
            bus_event = JoinCallIncomingRoomEvent(call.to_dict())
            self.bus.publish(bus_event)

    def join_call_incoming_room(self, event_objects, event):
        if event:
            args = event.get('args')
 
        if args[0] == 'dialed_from' or args[0] == 'blindtransfer':
            return

        channel = event_objects['channel']
        instance_name = args[0].strip()
        application_name = event.get('application')
        incoming_room_id = "{}.{}".format(application_name, instance_name)

        bridge_id = self.ari.asterisk.getGlobalVar(variable=incoming_room_id).get('value', None)

        if bridge_id:
            bridge = self.ari.bridges.get(bridgeId=bridge_id)
            if len(bridge.json.get('channels')) < 1:
                bridge.startMoh()
        else:
            bridge = self.ari.bridges.create(type='holding', name=incoming_room_id)
            bridge_id = bridge.id
            self.ari.asterisk.setGlobalVar(variable=incoming_room_id, value=bridge_id)
            bridge.startMoh()
        channel.answer()
        bridge.addChannel(bridgeId=bridge_id, channel=channel.id)
