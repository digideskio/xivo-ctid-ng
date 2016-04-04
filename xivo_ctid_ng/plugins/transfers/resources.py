# -*- coding: utf-8 -*-
# Copyright 2016 by Avencall
# SPDX-License-Identifier: GPL-3.0+

import uuid

from flask import request

from xivo_ctid_ng.core.auth import required_acl
from xivo_ctid_ng.core.rest_api import AuthResource


class TransfersResource(AuthResource):

    def __init__(self, transfers_service):
        self._transfers_service = transfers_service

    @required_acl('ctid-ng.transfers.create')
    def post(self):
        request_body = request.json
        transfer = self._transfers_service.create(request_body['transferred_call'],
                                                  request_body['initiator_call'],
                                                  request_body['context'],
                                                  request_body['exten'])
        return transfer.to_dict(), 201


class TransferResource(AuthResource):

    def __init__(self, transfers_service):
        self._transfers_service = transfers_service

    @required_acl('ctid-ng.transfers.{transfer_id}.read')
    def get(self, transfer_id):
        transfer = self._transfers_service.get(transfer_id)
        return transfer.to_dict(), 200

    @required_acl('ctid-ng.transfers.{transfer_id}.delete')
    def delete(self, transfer_id):
        self._transfers_service.cancel(transfer_id)
        return '', 204


class TransferCompleteResource(AuthResource):

    def __init__(self, transfers_service):
        self._transfers_service = transfers_service

    @required_acl('ctid-ng.transfers.{transfer_id}.complete.update')
    def put(self, transfer_id):
        self._transfers_service.complete(transfer_id)
        return '', 204
