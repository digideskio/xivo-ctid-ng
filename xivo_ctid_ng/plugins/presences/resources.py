# -*- coding: utf-8 -*-
# Copyright (C) 2016 Avencall
# SPDX-License-Identifier: GPL-3.0+

from flask import request
from marshmallow import Schema, fields

from xivo_ctid_ng.core.auth import required_acl
from xivo_ctid_ng.core.auth import get_token_user_uuid_from_request
from xivo_ctid_ng.core.rest_api import AuthResource


class UserPresenceRequestSchema(Schema):

    status_name = fields.Str(required=True)


class PresenceRequestSchema(UserPresenceRequestSchema):

    user_id = fields.Int(required=True)

user_presence_request_schema = UserPresenceRequestSchema(strict=True)
presence_request_schema = PresenceRequestSchema(strict=True)


class PresencesResource(AuthResource):

    def __init__(self, presences_service):
        self._presences_service = presences_service

    @required_acl('ctid-ng.presences.update')
    def put(self):
        request_body = presence_request_schema.load(request.get_json(force=True)).data

        self._presences_service.update_presence(request_body)

        return '', 204


class UserPresencesResource(AuthResource):

    def __init__(self, auth_client, presences_service):
        self._auth_client = auth_client
        self._presences_service = presences_service

    @required_acl('ctid-ng.users.me.presences.update')
    def put(self):
        request_body = user_presence_request_schema.load(request.get_json(force=True)).data

        user_id = get_token_user_uuid_from_request(self._auth_client)
        self._presences_service.update_presence(request_body, user_id)

        return '', 204
