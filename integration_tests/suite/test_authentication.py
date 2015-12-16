# -*- coding: utf-8 -*-
# Copyright 2015 by Avencall
# SPDX-License-Identifier: GPL-3.0+


from .base import IntegrationTest
from .base import INVALID_ACL_TOKEN, VALID_TOKEN

from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import equal_to


class TestAuthentication(IntegrationTest):

    asset = 'basic_rest'

    def test_no_auth_gives_401(self):
        result = self.get_call_result('my-call', token=None)

        assert_that(result.status_code, equal_to(401))

    def test_invalid_auth_gives_401(self):
        result = self.get_call_result('my-call', token='invalid-token')

        assert_that(result.status_code, equal_to(401))

    def test_invalid_acl_gives_401(self):
        result = self.get_call_result('my-call', token=INVALID_ACL_TOKEN)

        assert_that(result.status_code, equal_to(401))

    def test_valid_auth_gives_result(self):
        result = self.get_call_result('my-call', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(404))


class TestAuthenticationError(IntegrationTest):

    asset = 'no_auth_server'

    def test_no_auth_server_gives_503(self):
        result = self.get_call_result('my-call', token=None)

        assert_that(result.status_code, equal_to(503))
        assert_that(result.json()['reason'][0], contains_string('authentication server'))


class TestAuthenticationCoverage(IntegrationTest):

    asset = 'basic_rest'

    def test_auth_on_list_calls(self):
        result = self.get_calls_result()

        assert_that(result.status_code, equal_to(401))

    def test_auth_on_new_call(self):
        result = self.get_call_result('my-call')

        assert_that(result.status_code, equal_to(401))

    def test_auth_on_get_call(self):
        result = self.post_call_result(source=None, priority=None, extension=None, context=None)

        assert_that(result.status_code, equal_to(401))

    def test_auth_on_hangup(self):
        result = self.delete_call_result('my-call')

        assert_that(result.status_code, equal_to(401))

    def test_auth_on_list_plugins(self):
        result = self.get_plugins_result()

        assert_that(result.status_code, equal_to(401))
