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

logger = logging.getLogger(__name__)


class CoreCallControl(object):

    def __init__(self, config, queue):
        self.client = ari.connect(**config['connection'])
        self.callcontrol = CallControl(self.client, queue)

    def run(self):
        #self.client.on_channel_event('StasisStart', on_start)
        self.client.run(apps=['callcontrol'])

#def on_start(channel, event):
#    logger.info(channel)
#    logger.info(event)


class CallControl(object):

    def __init__(self, ari_client, queue):
        self.queue_callcontrol = queue
        self.ari = ari_client
        self.ari.on_channel_event('StasisStart', self.on_channel_event)

    def destroy(self):
        print "destroy..."

    def on_channel_event(self, channel_obj, event):
        channel = channel_obj.get('channel')
        args = event.get('args')
        print "channel:", channel
        print "event:", event
        #self.queue_callcontrol.put(channel)

        if not args:
            return

        channel.on_event('StasisStart', self.bridge_join(event, channel.id))

    def bridge_destroy(self, event):
        print "on destroy:", event
        if event.get('type') == 'StasisStart':
            return

        bridge = self.ari.bridges.destroy(bridgeId=event['args'][0])

    def bridge_join(self, event, channel):
        bridge = self.ari.bridges.get(bridgeId=event['args'][0])
	channel_id = bridge.json.get('channels')[0]
        self.ari.channels.ringStop(channelId=channel_id)
        bridge.addChannel(channel=channel)

        incoming = self.ari.channels.get(channelId=channel_id)
        incoming.on_event('StasisEnd', self.bridge_destroy(event))
        outgoing = self.ari.channels.get(channelId=channel)
        outgoing.on_event('StasisEnd', self.bridge_destroy(event))
