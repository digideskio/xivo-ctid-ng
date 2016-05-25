# -*- coding: utf-8 -*-
# Copyright 2016 by Avencall
# SPDX-License-Identifier: GPL-3.0+

import logging

from xivo_bus.resources.calls.transfer import (AnswerTransferEvent,
                                               CancelTransferEvent,
                                               CompleteTransferEvent,
                                               CreateTransferEvent,
                                               EndTransferEvent)

logger = logging.getLogger(__name__)


class TransferNotifier(object):

    def __init__(self, bus_producer):
        self._bus_producer = bus_producer

    def created(self, transfer):
        event = CreateTransferEvent(transfer.to_dict())
        self._bus_producer.publish(event)

    def answered(self, transfer):
        event = AnswerTransferEvent(transfer.to_dict())
        self._bus_producer.publish(event)

    def cancelled(self, transfer):
        event = CancelTransferEvent(transfer.to_dict())
        self._bus_producer.publish(event)

    def ended(self, transfer):
        event = EndTransferEvent(transfer.to_dict())
        self._bus_producer.publish(event)

    def completed(self, transfer):
        event = CompleteTransferEvent(transfer.to_dict())
        self._bus_producer.publish(event)
