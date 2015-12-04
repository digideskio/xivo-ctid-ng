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
        self.client.run(apps=['callcontrol'])

    def stop(self):
        self.client.close()


class CallControl(object):

    def __init__(self, ari_client, queue):
        self.queue_callcontrol = queue
        self.ari = ari_client
        self.ari.on_channel_event('StasisStart', self.on_channel_event_start)
        self.ari.on_channel_event('StasisEnd', self.on_channel_event_end)

    def on_channel_event_end(self, channel, event):
        print "channel left:", channel.id
        self.queue_callcontrol.put(_convert_event(event))

    def on_channel_event_start(self, channel_obj, event):
        channel = channel_obj.get('channel')
        self.queue_callcontrol.put(_convert_event(event))
        if event:
            args = event.get('args')

        if not args:
            return

        if args[0] == 'dialed':
            bridge_id = args[1]
            self.bridge_join(bridge_id, channel)

    def bridge_destroy(self, bridge_id):
        print "destroy bridge:", bridge_id
        bridge = self.ari.bridges.get(bridgeId=bridge_id)
        channels = bridge.json.get('channels')

        if channels:
            for channel_id in channels:
                self.ari.channels.hangup(channelId=channel_id)
        else:
            bridge.destroy()

    def safe_hangup(self, channel):
        print "hangup channel:", channel.id
        try:
            channel.hangup()
        except:
            pass

    def bridge_join(self, bridge_id, channel):
        bridge = self.ari.bridges.get(bridgeId=bridge_id)

        channelId = bridge.json.get('channels')[0]
        incoming = self.ari.channels.get(channelId=channelId)
        incoming.ringStop()
        channel.answer()

        bridge.addChannel(channel=channel.id)

        bridge.on_event('ChannelLeftBridge', lambda *args: self.bridge_destroy(bridge.id))

def _convert_event(event):
    result = Call(event['channel']['id'], event['channel']['creationtime'])
    result.creation_time = event['channel']['creationtime']
    result.bridges = []
    result.status = event['channel']['state']
    result.talking_to = []
    result.user_uuid = None
    result.event = event['type']
    result.application = event['application']

    return result.to_dict()

class Call(object):

    def __init__(self, id_, creation_time):
        self.id_ = id_
        self.creation_time = creation_time
        self.bridges = []
        self.status = 'Down'
        self.talking_to = []
        self.user_uuid = None
        self.event = None
        self.application = None

    def to_dict(self):
        return {
            'bridges': self.bridges,
            'call_id': self.id_,
            'creation_time': self.creation_time,
            'status': self.status,
            'talking_to': self.talking_to,
            'user_uuid': self.user_uuid,
            'event': self.event,
            'application': self.application,
        }
