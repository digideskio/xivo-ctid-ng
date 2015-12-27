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

from xivo_ctid_ng.core.rest_api import AuthResource

logger = logging.getLogger(__name__)


class WaitingRoomCallsResource(AuthResource):

    def __init__(self, calls_service):
        self.calls_service = calls_service

    def get(self, waiting_room_id):
        items = self.calls_service.list_calls(waiting_room_id)

        return items, 201

class WaitingRoomCallsAssociationResource(AuthResource):

    def __init__(self, calls_service):
        self.calls_service = calls_service

    def put(self, waiting_room_id, call_id):
        bridge_id = self.calls_service.add_call(waiting_room_id, call_id)

        return {'bridge_id': bridge_id}, 201

class WaitingRoomResource(AuthResource):

    def __init__(self, calls_service):
        self.calls_service = calls_service

    def post(self, waiting_room_id):
        bridge_id = self.calls_service.create_waiting_room(waiting_room_id)

        return {'bridge_id': bridge_id}, 201

    def delete(self, waiting_room_id, call_id):
        self.calls_service.delete_call_from_waiting_room(waiting_room_id, call_id)
