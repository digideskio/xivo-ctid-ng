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

from contextlib import contextmanager
from flask import request

from xivo_ctid_ng.core.auth import required_acl
from xivo_ctid_ng.core.rest_api import AuthResource

from . import validator
from .exceptions import AsteriskARIUnreachable

logger = logging.getLogger(__name__)


@contextmanager
def new_ari_client(config):
    try:
        yield ari.connect(**config)
    except requests.ConnectionError as e:
        raise AsteriskARIUnreachable(config, e)


class CallsResource(AuthResource):

    def __init__(self, calls_service):
        self.calls_service = calls_service

    @required_acl('ctid-ng.calls.list')
    def get(self):
        application_filter = request.args.get('application')
        application_instance_filter = request.args.get('application_instance')

        calls = self.calls_service.list_calls(application_filter, application_instance_filter)

        return {
            'items': [call.to_dict() for call in calls],
        }, 200

    @required_acl('ctid-ng.calls.originate')
    def post(self):
        request_body = request.json

        validator.validate_originate_body(request_body)

        call_id = self.calls_service.originate(request_body)

        return {'call_id': call_id}, 201


class CallResource(AuthResource):

    def __init__(self, calls_service):
        self.calls_service = calls_service

    @required_acl('ctid-ng.calls.get')
    def get(self, call_id):
        call = self.calls_service.get(call_id)

        return call.to_dict()

    @required_acl('ctid-ng.calls.hangup')
    def delete(self, call_id):
        self.calls_service.hangup(call_id)

        return None, 204

class AnswerResource(AuthResource):

    def __init__(self, calls_service):
        self.calls_service = calls_service

    def post(self, call_id):
        source_user = request.json['source']['user']

        self.calls_service.answer(source_user, call_id)


class BlindTransferResource(AuthResource):

    def __init__(self, calls_service):
        self.calls_service = calls_service

    def post(self, call_id, originator_call_id):
        destination_user = request.json['destination']['user']

        self.calls_service.transfer(destination_user, call_id, originator_call_id)


class BlindTransferAMIResource(AuthResource):

    def __init__(self, calls_service):
        self.calls_service = calls_service

    def post(self, call_id_transfered):
        context = request.json['destination']['dialplan']['context']
        exten = request.json['destination']['dialplan']['exten']

        print self.calls_service.transfer_via_ami(call_id_transfered, context, exten)

