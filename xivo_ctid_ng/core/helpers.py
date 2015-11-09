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

import calendar
import ari
import requests

from iso8601 import parse_date
from flask import current_app
from flask import request
from contextlib import contextmanager
from xivo_confd_client import Client as ConfdClient


@contextmanager
def new_confd_client(config):
    yield ConfdClient(**config)

@contextmanager
def new_ari_client(config):
    yield ari.connect(**config)


def endpoint_from_user_uuid(uuid):
    if current_app.config['auth']['token']:
        current_app.config['confd']['token'] = current_app.config['auth']['token']
    with new_confd_client(current_app.config['confd']) as confd:
        user_id = confd.users.get(uuid)['id']
        line_id = confd.users.relations(user_id).list_lines()['items'][0]['line_id']
        line = confd.lines.get(line_id)
        endpoint = "{}/{}".format(line['protocol'], line['name'])
    if endpoint:
        return endpoint

    return None


def get_uuid_from_call_id(ari, call_id):
    if current_app.config['auth']['token']:
        current_app.config['confd']['token'] = current_app.config['auth']['token']
    try:
        user_id = ari.channels.getChannelVar(channelId=call_id, variable='XIVO_USERID')['value']
    except:
        return None

    with new_confd_client(current_app.config['confd']) as confd:
        uuid = confd.users.get(user_id)['uuid']
        return uuid

    return None

def list_channels(args):
    application_filter = args.get('application')
    application_instance_filter = args.get('application_instance')

    with new_ari_client(current_app.config['ari']['connection']) as ari:
        if application_filter:
            try:
                channel_ids = ari.applications.get(applicationName=application_filter)['channel_ids']
            except requests.HTTPError:
                channel_ids = []
        else:
            channel_ids = [channel.id for channel in ari.channels.list()]

        return get_channel(channel_ids, ari)

    return None

def get_channel(channel_ids, ari, application_filter=None, application_instance_filter=None):
    calls = {}
    for channel_id in channel_ids:
        uuid = get_uuid_from_call_id(ari, channel_id)
        try:
            app_arg = ari.channels.getChannelVar(channelId=channel_id, variable='XIVO_STASIS_ARG')['value']
        except requests.HTTPError:
            app_arg = None
        channel = ari.channels.get(channelId=channel_id)
        if application_instance_filter is None or app_arg == application_instance_filter:
            calls[channel_id] = {'uuid': uuid,
                                 'status': channel.json.get('state'),
                                 'creationtime': iso2unix(channel.json.get('creationtime')),
                                 'application_arg': app_arg}

    return calls


def iso2unix(timestamp):
    parsed = parse_date(timestamp)
    timetuple = parsed.timetuple()
    return calendar.timegm(timetuple)
