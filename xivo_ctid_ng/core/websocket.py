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

import json
import logging
import os
import requests
import gevent
import ari

from datetime import timedelta
from flask import current_app
from flask import Flask
from flask import request
from flask_restful import Api
from flask_restful import Resource
from flask_cors import CORS
from contextlib import contextmanager
from werkzeug.contrib.fixers import ProxyFix
from xivo import http_helpers
from xivo_ctid_ng.core import auth
from xivo_ctid_ng.core import exceptions
from xivo_ctid_ng.core.helpers import get_channel
from xivo_ctid_ng.core.exceptions import APIException
from geventwebsocket.server import WebSocketServer
from geventwebsocket import WebSocketError

VERSION = 1.0

logger = logging.getLogger(__name__)
api = Api(prefix='/{}'.format(VERSION))


class CoreWebsocket(object):

    def __init__(self, config, queue):
        self.config = config
        self.call_control_queue = queue
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
        api.add_resource(Websocket, '/ws')
        self.api.init_app(self.app)

        self.app.config['queue'] = self.call_control_queue

        bind_addr = (self.config['listen'], self.config['port']+1)

        _check_file_readable(self.config['certificate'])
        _check_file_readable(self.config['private_key'])
        ssl = {
            'certfile': self.config['certificate'],
            'keyfile': self.config['private_key'],
            'ciphers': self.config.get('ciphers'),
        }

        server = WebSocketServer((bind_addr), self.app, **ssl)

        logger.debug('WSGIServer websocket starting... uid: %s, listen: %s:%s', os.getuid(), bind_addr[0], bind_addr[1])
        for route in http_helpers.list_routes(self.app):
            logger.debug(route)

        try:
            server.serve_forever()
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
def new_ari_client(config):
    yield ari.connect(**config)


class Websocket(AuthResource):

    def get(self):
        call_control = current_app.config['queue']
        print "Websocket open..."

        ws = request.environ.get('wsgi.websocket')
        if ws is None:
            return ["WebSocket connection is expected here."]

        message = {}

        try:
            while True:
                ws.receive()
                try:
                    message = call_control.get(block=False)
                except:
                    message = {}
                print ws.handler.server.clients.values()

                if message:
                    channels = message['channel']['id']
                    event_type = message['type']
                    if event_type == 'StasisStart':
                        with new_ari_client(current_app.config['ari']['connection']) as ari:
                            calls = get_channel([channels], ari)
                    else:
                        calls = {channels: { 'status': 'Down' }}

                    if calls:
                        ws.send(json.dumps(calls))

            ws.close()
        except WebSocketError, e:
            print "{0}: {1}".format(e.__class__.__name__, e)
