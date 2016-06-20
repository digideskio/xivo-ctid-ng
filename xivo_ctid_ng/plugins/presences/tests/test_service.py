# -*- coding: utf-8 -*-
# Copyright 2016 Avencall
# SPDX-License-Identifier: GPL-3.0+

import unittest
import uuid

from mock import Mock
from xivo_bus.resources.cti.event import UserStatusUpdateEvent

from xivo_ctid_ng.plugins.presences.services import PresencesService


class TestPresencesService(unittest.TestCase):

    def setUp(self):
        self.bus_publisher = Mock()
        self.xivo_uuid = 'xivo-uuid'
        self.service = PresencesService(self.bus_publisher)
        self.user_id = 1
        self.status_name = 'available'
        self.request_body = {
            'user_id': self.user_id,
            'status_name': self.status_name,
        }

    def test_update_presence(self):
        self.service.update_presence(self.request_body)

        expected_event = UserStatusUpdateEvent(self.user_id, self.status_name)
        self.bus_publisher.publish.assert_called_once_with(expected_event)

    def test_update_presence_without_user_id(self):
        del self.request_body['user_id']

        self.service.update_presence(self.request_body)

        expected_event = UserStatusUpdateEvent(self.user_id, self.status_name)
        self.bus_publisher.publish.assert_called_once_with(expected_event)

    def test_send_message_with_user_id(self):
        user_id = 1

        self.service.update_presence(self.request_body, user_id)

        expected_event = UserStatusUpdateEvent(self.user_id, self.status_name)
        self.bus_publisher.publish.assert_called_once_with(expected_event)
