# -*- coding: utf-8 -*-
# Copyright 2016 Avencall
# SPDX-License-Identifier: GPL-3.0+

import unittest
import uuid

from hamcrest import assert_that
from hamcrest import calling
from hamcrest import equal_to
from hamcrest import raises
from marshmallow import ValidationError

from xivo_ctid_ng.plugins.presences.resources import presence_request_schema
from xivo_ctid_ng.plugins.presences.resources import user_presence_request_schema


class TestUserPresenceRequestSchema(unittest.TestCase):

    schema = user_presence_request_schema

    def setUp(self):
        self.data = {
            'name': 'available'
        }

    def test_valid(self):
        result = self.schema.load(self.data).data

        assert_that(result['user_id'], equal_to(1))
        assert_that(result['name'], equal_to('available'))

    def test_invalid_name(self):
        self.data['name'] = None

        assert_that(calling(self.schema.load).with_args(self.data), raises(ValidationError))


class TestPresenceRequestSchema(unittest.TestCase):

    schema = presence_request_schema

    def setUp(self):
        self.data = {
            'user_id': 1,
            'name': 'available'
        }

    def test_valid(self):
        result = self.schema.load(self.data).data

        assert_that(result['user_id'], equal_to(1))
        assert_that(result['name'], equal_to('available'))

    def test_invalid_name(self):
        self.data['name'] = None

        assert_that(calling(self.schema.load).with_args(self.data), raises(ValidationError))

    def test_invalid_user_id(self):
        self.data['user_id'] = '1'

        assert_that(calling(self.schema.load).with_args(self.data), raises(ValidationError))
