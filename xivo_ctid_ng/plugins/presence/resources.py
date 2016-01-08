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

import logging

from flask import request

from xivo_ctid_ng.core.rest_api import AuthResource

logger = logging.getLogger(__name__)


class PresenceResource(AuthResource):

    def __init__(self, presence_service):
        self.presence_service = presence_service

    def put(self):
        request_body = request.json

        self.presence_service.send(request_body)

        return '', 204
