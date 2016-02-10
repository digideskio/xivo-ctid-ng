# -*- coding: UTF-8 -*-
# Copyright 2015 by Avencall
# SPDX-License-Identifier: GPL-3.0+


from .bus_consume import CallsBusEventHandler
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
        bus_consumer = dependencies['bus_consumer']
        bus_publisher = dependencies['bus_publisher']
        collectd = dependencies['collectd']
        token_changed_subscribe = dependencies['token_changed_subscribe']
        config = dependencies['config']

        calls_service = CallsService(config['ari']['connection'], config['confd'], ari, config['amid'], bus_publisher)
        token_changed_subscribe(calls_service.set_confd_token)

        calls_stasis = CallsStasis(ari.client, collectd, bus_publisher, calls_service, config['uuid'])
        calls_stasis.subscribe()

        calls_bus_event_handler = CallsBusEventHandler(ari.client, collectd, bus_publisher, calls_service, config['uuid'])
        calls_bus_event_handler.subscribe(bus_consumer)

        api.add_resource(CallsResource, '/calls', resource_class_args=[calls_service])
        api.add_resource(CallResource, '/calls/<call_id>', resource_class_args=[calls_service])
        api.add_resource(ConnectCallToUserResource, '/calls/<call_id>/user/<user_uuid>', resource_class_args=[calls_service])
        api.add_resource(BlindTransferResource, '/calls/<call_id>/transfer/<originator_call_id>/blind', resource_class_args=[calls_service])
        api.add_resource(BlindTransferAMIResource, '/calls/<call_id_transfered>/transfer/ami/blind', resource_class_args=[calls_service])
        api.add_resource(AttendedTransferAMIResource, '/calls/<call_id_transfered>/transfer/ami/attended', resource_class_args=[calls_service])
        api.add_resource(ConvertChannelToStasis, '/calls/<call_id>/stasis', resource_class_args=[calls_service])
