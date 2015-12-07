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

from xivo_ctid_ng.core.exceptions import APIException


class AsteriskARIUnreachable(APIException):

    def __init__(self, asterisk_ari_config, error):
        super(AsteriskARIUnreachable, self).__init__(
            status_code=503,
            message='Asterisk ARI server unreachable',
            error_id='asterisk-ari-unreachable',
            details={
                'asterisk_ari_config': asterisk_ari_config,
                'original_error': str(error),
            }
        )
