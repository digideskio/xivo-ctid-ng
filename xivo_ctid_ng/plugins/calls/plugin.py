# -*- coding: UTF-8 -*-
# Copyright 2015 by Avencall
# SPDX-License-Identifier: GPL-3.0+


from .resources import CallResource
from .resources import CallsResource
from .resources import ConnectCallToUserResource
from .resources import BlindTransferResource
from .resources import BlindTransferAMIResource
from .resources import AttendedTransferAMIResource
from .resources import ConvertChannelToStasis
from .services import CallsService
from .stasis import CallsStasis


class Plugin(object):

    def load(self, dependencies):
        api = dependencies['api']
        ari = dependencies['ari']
        bus = dependencies['bus']
        token_changed_subscribe = dependencies['token_changed_subscribe']
        config = dependencies['config']

        calls_service = CallsService(config['ari']['connection'], config['confd'], ari, amid_config=config['amid'])
        token_changed_subscribe(calls_service.set_confd_token)

        calls_stasis = CallsStasis(ari.client, bus, calls_service)
        calls_stasis.subscribe()

        api.add_resource(CallsResource, '/calls', resource_class_args=[calls_service])
        api.add_resource(CallResource, '/calls/<call_id>', resource_class_args=[calls_service])
        api.add_resource(ConnectCallToUserResource, '/calls/<call_id>/user/<user_id>', resource_class_args=[calls_service])
        api.add_resource(BlindTransferResource, '/calls/<call_id>/transfer/<originator_call_id>/blind', resource_class_args=[calls_service])
        api.add_resource(BlindTransferAMIResource, '/calls/<call_id_transfered>/transfer/ami/blind', resource_class_args=[calls_service])
        api.add_resource(AttendedTransferAMIResource, '/calls/<call_id_transfered>/transfer/ami/attended', resource_class_args=[calls_service])
        api.add_resource(ConvertChannelToStasis, '/calls/<call_id>/stasis', resource_class_args=[calls_service])
