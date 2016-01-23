# -*- coding: utf-8 -*-
# Copyright 2015 by Avencall
# SPDX-License-Identifier: GPL-3.0+

import logging

logger = logging.getLogger(__name__)


class CallsStasis(object):

    def __init__(self, ari_client, bus_publisher, services):
        self.ari = ari_client
        self.bus_publisher = bus_publisher
        self.services = services

    def subscribe(self):
        self.ari.on_channel_event('StasisStart', self.bridge_connect_user)
        self.ari.on_channel_event('ChannelLeftBridge', self.relay_channel_bridge_left)

    def relay_channel_bridge_left(self, channel, event):
        logger.debug('Relaying to bus: channel %s left bridge', channel.id)
        if event.get('bridge').get('bridge_type') == 'mixing' and not event.get('bridge').get('name'):
            channel_ids = event.get('bridge').get('channels', None)
            if channel_ids:
                for chan in channel_ids:
                    channel = self.ari.channels.get(channelId=chan)
                    channel.hangup()

    def bridge_connect_user(self, event_objects, event):
        if not event.get('args'):
            return

        channel = event_objects['channel']
        if event['args'][0] == 'dialed_from':
            originator_channel_id = event['args'][1]
            originator_channel = self.ari.channels.get(channelId=originator_channel_id)
            channel.answer()
            originator_channel.answer()
            this_channel_id = channel.id
            bridge = self.ari.bridges.create(type='mixing')
            bridge.addChannel(channel=originator_channel_id)
            bridge.addChannel(channel=this_channel_id)
