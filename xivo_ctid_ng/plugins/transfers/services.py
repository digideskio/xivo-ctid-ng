# -*- coding: utf-8 -*-
# Copyright 2016 by Avencall
# SPDX-License-Identifier: GPL-3.0+

import logging
import uuid

from contextlib import contextmanager
from requests import RequestException
from xivo.caller_id import assemble_caller_id
from xivo_amid_client import Client as AmidClient
from xivo_ctid_ng.core.ari_ import APPLICATION_NAME
from ari.exceptions import ARINotFound
from ari.exceptions import ARINotInStasis

from .exceptions import NoSuchTransfer
from .exceptions import TransferCreationError
from .exceptions import TransferCancellationError
from .exceptions import TransferCompletionError
from .exceptions import XiVOAmidUnreachable
from .transfer import Transfer, TransferStatus

logger = logging.getLogger(__name__)


@contextmanager
def new_amid_client(config):
    yield AmidClient(**config)


class TransfersService(object):
    def __init__(self, ari, amid_config, state_persistor):
        self.ari = ari
        self.amid_config = amid_config
        self.state_persistor = state_persistor

    def set_token(self, auth_token):
        self.auth_token = auth_token

    def create(self, transferred_call, initiator_call, context, exten):
        try:
            transferred_channel = self.ari.channels.get(channelId=transferred_call)
            initiator_channel = self.ari.channels.get(channelId=initiator_call)
        except ARINotFound:
            raise TransferCreationError('channel not found')
        except ARINotInStasis:
            transfer_id = str(uuid.uuid4())
            self.convert_transfer_to_stasis(transferred_call, initiator_call, context, exten, transfer_id)
            transfer = Transfer(transfer_id)
            transfer.initiator_call = initiator_call
            transfer.transferred_call = transferred_call
            transfer.status = TransferStatus.starting
        else:
            transfer_bridge = self.ari.bridges.create(type='mixing', name='transfer')
            transfer_id = transfer_bridge.id
            try:
                transferred_channel.setChannelVar(variable='XIVO_TRANSFER_ROLE', value='transferred')
                transferred_channel.setChannelVar(variable='XIVO_TRANSFER_ID', value=transfer_id)
                initiator_channel.setChannelVar(variable='XIVO_TRANSFER_ROLE', value='initiator')
                initiator_channel.setChannelVar(variable='XIVO_TRANSFER_ID', value=transfer_id)
                transfer_bridge.addChannel(channel=transferred_call)
                transfer_bridge.addChannel(channel=initiator_call)
            except ARINotFound:
                raise TransferCreationError('some channel got hung up')

            try:
                self.hold_transferred_call(transferred_call)
            except ARINotFound:
                raise TransferCreationError('transferred call hung up')

            recipient_call = self.originate_recipient(initiator_call, context, exten, transfer_id)

            transfer = Transfer(transfer_id)
            transfer.transferred_call = transferred_call
            transfer.initiator_call = initiator_call
            transfer.recipient_call = recipient_call
            transfer.status = TransferStatus.ringback

        self.state_persistor.upsert(transfer)
        return transfer

    def hold_transferred_call(self, transferred_call):
        self.ari.channels.mute(channelId=transferred_call, direction='in')
        self.ari.channels.hold(channelId=transferred_call)
        self.ari.channels.startMoh(channelId=transferred_call)

    def unhold_transferred_call(self, transferred_call):
        self.ari.channels.unmute(channelId=transferred_call, direction='in')
        self.ari.channels.unhold(channelId=transferred_call)
        self.ari.channels.stopMoh(channelId=transferred_call)

    def originate_recipient(self, initiator_call, context, exten, transfer_id):
        try:
            app_instance = self.ari.channels.getChannelVar(channelId=initiator_call, variable='XIVO_STASIS_ARGS')['value']
        except ARINotFound:
            raise TransferCreationError('{call}: no app_instance found'.format(call=initiator_call))
        initiator_channel = self.ari.channels.get(channelId=initiator_call)
        caller_id = assemble_caller_id(initiator_channel.json['caller']['name'], initiator_channel.json['caller']['number'])
        recipient_endpoint = 'Local/{exten}@{context}'.format(exten=exten, context=context)
        app_args = [app_instance, 'transfer_recipient_called', transfer_id]
        originate_variables = {'XIVO_TRANSFER_ROLE': 'recipient',
                               'XIVO_TRANSFER_ID': transfer_id,
                               'XIVO_HANGUP_LOCK_TARGET': initiator_call}
        new_channel = self.ari.channels.originate(endpoint=recipient_endpoint,
                                                  app=APPLICATION_NAME,
                                                  appArgs=app_args,
                                                  callerId=caller_id,
                                                  variables={'variables': originate_variables})
        recipient_call = new_channel.id
        try:
            initiator_channel.setChannelVar(variable='CONNECTEDLINE(name)', value=new_channel.json['caller']['name'])
            initiator_channel.setChannelVar(variable='CONNECTEDLINE(num)', value=new_channel.json['caller']['number'])
            initiator_channel.setChannelVar(variable='XIVO_HANGUP_LOCK_SOURCE', value=recipient_call)
        except ARINotFound:
            raise TransferCreationError('initiator hung up')
        return recipient_call

    def get(self, transfer_id):
        try:
            return self.state_persistor.get(transfer_id)
        except KeyError:
            raise NoSuchTransfer(transfer_id)

    def complete(self, transfer_id):
        transfer = self.get(transfer_id)

        try:
            self.ari.channels.setChannelVar(channelId=transfer.transferred_call, variable='XIVO_TRANSFER_ID', value='')
            self.ari.channels.setChannelVar(channelId=transfer.transferred_call, variable='XIVO_TRANSFER_ROLE', value='')
        except ARINotFound:
            pass

        try:
            self.ari.channels.setChannelVar(channelId=transfer.recipient_call, variable='XIVO_TRANSFER_ID', value='')
            self.ari.channels.setChannelVar(channelId=transfer.recipient_call, variable='XIVO_TRANSFER_ROLE', value='')
        except ARINotInStasis:
            pass
        except ARINotFound:
            raise TransferCompletionError(transfer_id, 'transfer recipient hung up')

        self.state_persistor.remove(transfer_id)
        if transfer.initiator_call:
            try:
                self.ari.channels.hangup(channelId=transfer.initiator_call)
            except ARINotFound:
                pass
        try:
            self.unhold_transferred_call(transfer.transferred_call)
        except ARINotFound:
            raise TransferCompletionError(transfer_id, 'transferred hung up')

    def cancel(self, transfer_id):
        transfer = self.get(transfer_id)

        try:
            self.ari.channels.setChannelVar(channelId=transfer.transferred_call, variable='XIVO_TRANSFER_ID', value='')
            self.ari.channels.setChannelVar(channelId=transfer.transferred_call, variable='XIVO_TRANSFER_ROLE', value='')
        except ARINotFound:
            pass

        try:
            self.ari.channels.setChannelVar(channelId=transfer.initiator_call, variable='XIVO_TRANSFER_ID', value='')
            self.ari.channels.setChannelVar(channelId=transfer.initiator_call, variable='XIVO_TRANSFER_ROLE', value='')
        except ARINotFound:
            raise TransferCancellationError(transfer_id, 'initiator hung up')

        self.state_persistor.remove(transfer_id)
        if transfer.recipient_call:
            try:
                self.ari.channels.hangup(channelId=transfer.recipient_call)
            except ARINotFound:
                pass

        try:
            self.unhold_transferred_call(transfer.transferred_call)
        except ARINotFound:
            raise TransferCancellationError(transfer_id, 'transferred hung up')

    def abandon(self, transfer_id):
        transfer = self.get(transfer_id)

        try:
            self.ari.channels.setChannelVar(channelId=transfer.recipient_call, variable='XIVO_TRANSFER_ID', value='')
            self.ari.channels.setChannelVar(channelId=transfer.recipient_call, variable='XIVO_TRANSFER_ROLE', value='')
        except (ARINotFound, ARINotInStasis):
            pass
        try:
            self.ari.channels.setChannelVar(channelId=transfer.initiator_call, variable='XIVO_TRANSFER_ID', value='')
            self.ari.channels.setChannelVar(channelId=transfer.initiator_call, variable='XIVO_TRANSFER_ROLE', value='')
        except ARINotFound:
            pass

        self.state_persistor.remove(transfer_id)
        if transfer.transferred_call:
            try:
                self.ari.channels.hangup(channelId=transfer.transferred_call)
            except ARINotFound:
                pass

    def convert_transfer_to_stasis(self, transferred_call, initiator_call, context, exten, transfer_id):
        set_variables = [(transferred_call, 'XIVO_TRANSFER_ROLE', 'transferred'),
                         (transferred_call, 'XIVO_TRANSFER_ID', transfer_id),
                         (transferred_call, 'XIVO_TRANSFER_DESTINATION_CONTEXT', context),
                         (transferred_call, 'XIVO_TRANSFER_DESTINATION_EXTEN', exten),
                         (initiator_call, 'XIVO_TRANSFER_ROLE', 'initiator'),
                         (initiator_call, 'XIVO_TRANSFER_ID', transfer_id),
                         (initiator_call, 'XIVO_TRANSFER_DESTINATION_CONTEXT', context),
                         (initiator_call, 'XIVO_TRANSFER_DESTINATION_EXTEN', exten)]
        with new_amid_client(self.amid_config) as ami:
            try:
                for channel_id, variable, value in set_variables:
                    parameters = {'Channel': channel_id,
                                  'Variable': variable,
                                  'Value': value}
                    ami.action('Setvar', parameters, token=self.auth_token)

                destination = {'Channel': transferred_call,
                               'ExtraChannel': initiator_call,
                               'Context': 'convert_to_stasis',
                               'Exten': 'transfer',
                               'Priority': 1}
                ami.action('Redirect', destination, token=self.auth_token)
            except RequestException as e:
                raise XiVOAmidUnreachable(self.amid_config, e)
