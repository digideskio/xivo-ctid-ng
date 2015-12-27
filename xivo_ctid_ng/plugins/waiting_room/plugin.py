# -*- coding: UTF-8 -*-

# Copyright (C) 2015 Avencall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from .resources import WaitingRoomResource
from .resources import WaitingRoomCallsResource
from .resources import WaitingRoomCallsAssociationResource
from .services import WaitingRoomCallsService
from .stasis import WaitingRoomCallsStasis


class Plugin(object):

    def load(self, dependencies):
        api = dependencies['api']
        ari = dependencies['ari']
        bus = dependencies['bus']
        config = dependencies['config']

        calls_service = WaitingRoomCallsService(config['ari']['connection'], ari, bus)
        calls_stasis = WaitingRoomCallsStasis(ari.client, bus, calls_service)
        calls_stasis.subscribe()

        api.add_resource(WaitingRoomResource, '/hold/<waiting_room_id>', resource_class_args=[calls_service])
        api.add_resource(WaitingRoomCallsResource, '/hold/<waiting_room_id>/calls', resource_class_args=[calls_service])
        api.add_resource(WaitingRoomCallsAssociationResource, '/hold/<waiting_room_id>/calls/<call_id>', resource_class_args=[calls_service])
