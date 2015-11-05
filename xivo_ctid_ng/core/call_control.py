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
        print "channel:", channel
        if event:
            args = event.get('args')
            print "event:", event
        #self.queue_callcontrol.put(channel)

        if not args:
            return

        channel.on_event('StasisStart', self.bridge_join(event, channel))

    def bridge_destroy(self, bridge):
        print "destroy bridge:", bridge.id
        for channel in bridge.json.get('channels'):
            try:
                self.ari.channels.hangup(channelId=channel)
            except:
                pass

        try:
            bridge.destroy()
        except:
            pass

    def safe_hangup(self, channel):
        print "hangup channel:", channel.id
        try:
            channel.hangup()
        except:
            pass

    def bridge_join(self, event, channel):
        bridgeId = event.get('args')[0]
        bridge = self.ari.bridges.get(bridgeId=bridgeId)

	channelId = bridge.json.get('channels')[0]
        incoming = self.ari.channels.get(channelId=channelId)
        incoming.ringStop()

        bridge.addChannel(channel=channel.id)

        incoming.on_event('StasisEnd', lambda *args: self.safe_hangup(incoming))
        channel.on_event('StasisEnd', lambda *args: self.safe_hangup(channel))
        bridge.on_event('ChannelLeftBridge', lambda *args: self.bridge_destroy(bridge))
