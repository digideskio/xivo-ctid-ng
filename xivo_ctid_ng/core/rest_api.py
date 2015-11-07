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

from datetime import timedelta
from iso8601 import parse_date
import calendar

import ari
import logging
import os
import requests

from cherrypy import wsgiserver
from flask import current_app
from flask import Flask
from flask import request
from flask_restful import Api
from flask_restful import Resource
from flask_cors import CORS
from contextlib import contextmanager
from werkzeug.contrib.fixers import ProxyFix
from xivo import http_helpers
from xivo_confd_client import Client as ConfdClient
from xivo_ctid_ng.core import auth
from xivo_ctid_ng.core import exceptions
from xivo_ctid_ng.core.exceptions import APIException
from xivo_ctid_ng.resources.api.actions import SwaggerResource

VERSION = 1.0

logger = logging.getLogger(__name__)
api = Api(prefix='/{}'.format(VERSION))


class CoreRestApi(object):

    def __init__(self, config):
        self.config = config
        self.app = Flask('xivo_ctid_ng')
        http_helpers.add_logger(self.app, logger)
        self.app.after_request(http_helpers.log_request)
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app)
        self.app.secret_key = os.urandom(24)
        self.app.permanent_session_lifetime = timedelta(minutes=5)
        self.load_cors()
        self.api = api

    def load_cors(self):
        cors_config = dict(self.config.get('cors', {}))
        enabled = cors_config.pop('enabled', False)
        if enabled:
            CORS(self.app, **cors_config)

    def run(self):
        api.add_resource(Calls, '/calls')
        api.add_resource(Call, '/calls/<call_id>')
        api.add_resource(Answer, '/calls/<call_id>/answer')
        SwaggerResource.add_resource(api)

        self.api.init_app(self.app)

        bind_addr = (self.config['listen'], self.config['port'])

        _check_file_readable(self.config['certificate'])
        _check_file_readable(self.config['private_key'])
        wsgi_app = wsgiserver.WSGIPathInfoDispatcher({'/': self.app})
        server = wsgiserver.CherryPyWSGIServer(bind_addr=bind_addr,
                                               wsgi_app=wsgi_app)
        server.ssl_adapter = http_helpers.ssl_adapter(self.config['certificate'],
                                                      self.config['private_key'],
                                                      self.config.get('ciphers'))
        logger.debug('WSGIServer starting... uid: %s, listen: %s:%s', os.getuid(), bind_addr[0], bind_addr[1])
        for route in http_helpers.list_routes(self.app):
            logger.debug(route)

        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()


def _check_file_readable(file_path):
    with open(file_path, 'r'):
        pass


class ErrorCatchingResource(Resource):
    method_decorators = [exceptions.handle_api_exception] + Resource.method_decorators


class AuthCheckResource(ErrorCatchingResource):
    method_decorators = [auth.verify_token] + ErrorCatchingResource.method_decorators

class AuthResource(AuthCheckResource):
    method_decorators = [auth.get_token] + AuthCheckResource.method_decorators

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

def iso2unix(timestamp):
    parsed = parse_date(timestamp)
    timetuple = parsed.timetuple()
    return calendar.timegm(timetuple)

class NoSuchCall(APIException):

    def __init__(self, call_id):
        super(NoSuchCall, self).__init__(
            status_code=404,
            message='No such call',
            error_id='no-such-call',
            details={
                'call_id': call_id
            }
        )


class Calls(AuthResource):

    def get(self):
        application_filter = request.args.get('application')
        application_instance_filter = request.args.get('application_instance')

        with new_ari_client(current_app.config['ari']['connection']) as ari:
            if application_filter:
                try:
                    channel_ids = ari.applications.get(applicationName=application_filter)['channel_ids']
                except requests.HTTPError:
                    channel_ids = []
            else:
                channel_ids = [channel.id for channel in ari.channels.list()]

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

        return calls, 200

    def post(self):
        request_body = request.json
        endpoint = endpoint_from_user_uuid(request_body['source']['user'])
        with new_ari_client(current_app.config['ari']['connection']) as ari:
            call = ari.channels.originate(endpoint=endpoint,
                                          extension=request_body['destination']['extension'],
                                          context=request_body['destination']['context'],
                                          priority=request_body['destination']['priority'])
            return {'call_id': call.id}, 201

        return None


class Call(AuthResource):

    def get(self, call_id):
        with new_ari_client(current_app.config['ari']['connection']) as ari:
            try:
                channel = ari.channels.get(channelId=call_id)
            except requests.RequestException:
                raise NoSuchCall(call_id)

            bridges = [bridge.id for bridge in ari.bridges.list() if channel.id in bridge.json.get('channels')]

            talking_to = dict()
            for bridge_id in bridges:
                calls = ari.bridges.get(bridgeId=bridge_id).json.get('channels')
                for call in calls:
                    uuid = get_uuid_from_call_id(ari, call)
                    talking_to[call] = uuid
                del talking_to[call_id]

        return {
            'status': channel.json.get('state'),
            'creationtime': iso2unix(channel.json.get('creationtime')),
            'talking_to': dict(talking_to),
            'bridges': bridges,
        }

    def delete(self, call_id):
        with new_ari_client(current_app.config['ari']['connection']) as ari:
            try:
                ari.channels.hangup(channelId=call_id)
            except requests.RequestException:
                raise NoSuchCall(call_id)

        return None, 204


class Answer(AuthResource):

    def post(self, call_id):
        request_body = request.json
        endpoint = endpoint_from_user_uuid(request_body['source']['user'])

        with new_ari_client(current_app.config['ari']['connection']) as ari:
            ari.channels.answer(channelId=call_id)
            ari.channels.ring(channelId=call_id)
            bridge = ari.bridges.create(type='mixing')
            bridge.addChannel(channel=call_id)
            params = ['dialed', bridge.id]
            ari.channels.originate(endpoint=endpoint,
                                   app='callcontrol',
                                   appArgs=params)
