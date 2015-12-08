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

from .resources import CallResource, CallsResource, AnswerResource, BlindTransferResource


class Plugin(object):

    def load(self, dependencies):
        api = dependencies['api']
        api.add_resource(CallsResource, '/calls')
        api.add_resource(CallResource, '/calls/<call_id>')
        api.add_resource(AnswerResource, '/calls/<call_id>/answer')
        api.add_resource(BlindTransferResource, '/calls/<call_id>/transfer/<originator_call_id>/blind')
