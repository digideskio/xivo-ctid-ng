# -*- coding: UTF-8 -*-
# Copyright 2016 by Avencall
# SPDX-License-Identifier: GPL-3.0+

from xivo_amid_client import Client as AmidClient
from xivo_auth_client import Client as AuthClient
from xivo_confd_client import Client as ConfdClient

from .notifier import TransferNotifier
from .resources import TransferResource
from .resources import TransferCompleteResource
from .resources import TransfersResource
from .resources import UserTransfersResource
from .services import TransfersService
from .stasis import TransfersStasis
from .state import state_factory
from .state_persistor import StatePersistor


class Plugin(object):

    def load(self, dependencies):
        api = dependencies['api']
        ari = dependencies['ari']
        bus_publisher = dependencies['bus_publisher']
        config = dependencies['config']
        token_changed_subscribe = dependencies['token_changed_subscribe']

        amid_client = AmidClient(**config['amid'])
        auth_client = AuthClient(**config['auth'])
        confd_client = ConfdClient(**config['confd'])

        token_changed_subscribe(amid_client.set_token)
        token_changed_subscribe(confd_client.set_token)

        state_persistor = StatePersistor(ari.client)

        transfers_service = TransfersService(amid_client, ari.client, confd_client, state_factory, state_persistor)

        transfers_stasis = TransfersStasis(amid_client, ari.client, transfers_service, state_factory, state_persistor, config['uuid'])
        transfers_stasis.subscribe()

        notifier = TransferNotifier(bus_publisher)

        state_factory.set_dependencies(amid_client, ari.client, notifier, transfers_service, state_persistor)

        api.add_resource(TransfersResource, '/transfers', resource_class_args=[transfers_service])
        api.add_resource(TransferResource, '/transfers/<transfer_id>', resource_class_args=[transfers_service])
        api.add_resource(TransferCompleteResource, '/transfers/<transfer_id>/complete', resource_class_args=[transfers_service])
        api.add_resource(UserTransfersResource, '/users/me/transfers', resource_class_args=[auth_client, transfers_service])
