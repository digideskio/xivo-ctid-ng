# -*- coding: utf-8 -*-
# Copyright 2015 by Avencall
# SPDX-License-Identifier: GPL-3.0+

from hamcrest import assert_that
from hamcrest import contains
from hamcrest import contains_inanyorder
from hamcrest import empty
from hamcrest import equal_to
from hamcrest import has_entries
from hamcrest import has_entry
from hamcrest import has_item
from hamcrest import has_items
from hamcrest import contains_string
from xivo_test_helpers import until

from .base import IntegrationTest
from .base import MockApplication
from .base import MockBridge
from .base import MockChannel
from .base import MockLine
from .base import MockUser
from .base import MockUserLine
from .base import VALID_TOKEN


class TestListCalls(IntegrationTest):

    asset = 'basic_rest'

    def setUp(self):
        super(TestListCalls, self).setUp()
        self.reset_ari()
        self.reset_confd()

    def test_given_no_calls_when_list_calls_then_empty_list(self):
        calls = self.list_calls()

        assert_that(calls, has_entry('items', contains()))

    def test_given_some_calls_and_no_user_id_when_list_calls_then_list_calls_with_no_user_uuid(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))

        calls = self.list_calls()

        assert_that(calls, has_entry('items', contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'user_uuid': None}),
            has_entries({'call_id': 'second-id',
                         'user_uuid': None}))))

    def test_given_some_calls_with_user_id_when_list_calls_then_list_calls_with_user_uuid(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))
        self.set_ari_channel_variable({'first-id': {'XIVO_USERID': 'user1-id'},
                                       'second-id': {'XIVO_USERID': 'user2-id'}})
        self.set_confd_users(MockUser(id='user1-id', uuid='user1-uuid'),
                             MockUser(id='user2-id', uuid='user2-uuid'))

        calls = self.list_calls()

        assert_that(calls, has_entry('items', contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'user_uuid': 'user1-uuid'}),
            has_entries({'call_id': 'second-id',
                         'user_uuid': 'user2-uuid'}))))

    def test_given_some_calls_when_list_calls_then_list_calls_with_status(self):
        self.set_ari_channels(MockChannel(id='first-id', state='Up'),
                              MockChannel(id='second-id', state='Ringing'))

        calls = self.list_calls()

        assert_that(calls, has_entry('items', contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'status': 'Up'}),
            has_entries({'call_id': 'second-id',
                         'status': 'Ringing'}))))

    def test_given_some_calls_when_list_calls_then_list_calls_with_bridges(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))
        self.set_ari_bridges(MockBridge(id='first-bridge', channels=['first-id']),
                             MockBridge(id='second-bridge', channels=['second-id']))

        calls = self.list_calls()

        assert_that(calls, has_entry('items', contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'bridges': ['first-bridge']}),
            has_entries({'call_id': 'second-id',
                         'bridges': ['second-bridge']}))))

    def test_given_some_calls_when_list_calls_then_list_calls_with_talking_channels_and_users(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))
        self.set_ari_bridges(MockBridge(id='bridge-id', channels=['first-id', 'second-id']))
        self.set_ari_channel_variable({'first-id': {'XIVO_USERID': 'user1-id'},
                                       'second-id': {'XIVO_USERID': 'user2-id'}})
        self.set_confd_users(MockUser(id='user1-id', uuid='user1-uuid'),
                             MockUser(id='user2-id', uuid='user2-uuid'))

        calls = self.list_calls()

        assert_that(calls, has_entry('items', contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'talking_to': {'second-id': 'user2-uuid'}}),
            has_entries({'call_id': 'second-id',
                         'talking_to': {'first-id': 'user1-uuid'}}))))

    def test_given_some_calls_when_list_calls_then_list_calls_with_creation_time(self):
        self.set_ari_channels(MockChannel(id='first-id', creation_time='first-time'),
                              MockChannel(id='second-id', creation_time='second-time'))

        calls = self.list_calls()

        assert_that(calls, has_entry('items', contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'creation_time': 'first-time'}),
            has_entries({'call_id': 'second-id',
                         'creation_time': 'second-time'}))))

    def test_given_some_calls_when_list_calls_then_list_calls_with_caller_id(self):
        self.set_ari_channels(MockChannel(id='first-id', caller_id_name='Weber', caller_id_number='4185556666'),
                              MockChannel(id='second-id', caller_id_name='Denis', caller_id_number='4185557777'))

        calls = self.list_calls()

        assert_that(calls, has_entry('items', contains_inanyorder(
            has_entries({'call_id': 'first-id',
                         'caller_id_number': '4185556666',
                         'caller_id_name': 'Weber'}),
            has_entries({'call_id': 'second-id',
                         'caller_id_number': '4185557777',
                         'caller_id_name': 'Denis'}))))

    def test_given_some_calls_when_list_calls_by_application_then_list_of_calls_is_filtered(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'),
                              MockChannel(id='third-id'))
        self.set_ari_applications(MockApplication(name='my-app', channels=['first-id', 'third-id']))

        calls = self.list_calls(application='my-app')

        assert_that(calls, has_entry('items', contains_inanyorder(
            has_entries({'call_id': 'first-id'}),
            has_entries({'call_id': 'third-id'}))))

    def test_given_some_calls_and_no_applications_when_list_calls_by_application_then_no_calls(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))

        calls = self.list_calls(application='my-app', token=VALID_TOKEN)

        assert_that(calls, has_entry('items', empty()))

    def test_given_some_calls_when_list_calls_by_application_instance_then_list_of_calls_is_filtered(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'),
                              MockChannel(id='third-id'),
                              MockChannel(id='fourth-id'))
        self.set_ari_applications(MockApplication(name='my-app', channels=['first-id', 'second-id', 'third-id']))
        self.set_ari_channel_variable({'first-id': {'XIVO_STASIS_ARGS': 'appX'},
                                       'second-id': {'XIVO_STASIS_ARGS': 'appY'},
                                       'third-id': {'XIVO_STASIS_ARGS': 'appX'}})

        calls = self.list_calls(application='my-app', application_instance='appX')

        assert_that(calls, has_entry('items', contains_inanyorder(
            has_entries({'call_id': 'first-id'}),
            has_entries({'call_id': 'third-id'}))))


class TestGetCall(IntegrationTest):

    asset = 'basic_rest'

    def setUp(self):
        super(TestGetCall, self).setUp()
        self.reset_ari()
        self.reset_confd()

    def test_given_no_calls_when_get_call_then_404(self):
        call_id = 'not-found'

        result = self.get_call_result(call_id, token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(404))

    def test_given_one_call_when_get_call_then_get_call(self):
        self.set_ari_channels(MockChannel(id='first-id', state='Up', creation_time='first-time', caller_id_name='Weber', caller_id_number='4185559999'),
                              MockChannel(id='second-id'))
        self.set_ari_bridges(MockBridge(id='bridge-id', channels=['first-id', 'second-id']))
        self.set_ari_channel_variable({'first-id': {'XIVO_USERID': 'user1-id'},
                                       'second-id': {'XIVO_USERID': 'user2-id'}})
        self.set_confd_users(MockUser(id='user1-id', uuid='user1-uuid'),
                             MockUser(id='user2-id', uuid='user2-uuid'))

        call = self.get_call('first-id')

        assert_that(call, has_entries({
            'call_id': 'first-id',
            'user_uuid': 'user1-uuid',
            'status': 'Up',
            'talking_to': {
                'second-id': 'user2-uuid'
            },
            'bridges': contains('bridge-id'),
            'creation_time': 'first-time',
            'caller_id_name': 'Weber',
            'caller_id_number': '4185559999',
        }))


class TestDeleteCall(IntegrationTest):

    asset = 'basic_rest'

    def setUp(self):
        super(TestDeleteCall, self).setUp()
        self.reset_ari()
        self.reset_confd()

    def test_given_no_calls_when_delete_call_then_404(self):
        call_id = 'not-found'

        result = self.delete_call_result(call_id, token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(404))

    def test_given_one_call_when_delete_call_then_call_hungup(self):
        call_id = 'call-id'
        self.set_ari_channels(MockChannel(id=call_id, state='Up'))

        self.hangup_call(call_id)

        assert_that(self.ari_requests(), has_entry('requests', has_item(has_entries({
            'method': 'DELETE',
            'path': '/ari/channels/call-id',
        }))))


class TestCreateCall(IntegrationTest):

    asset = 'basic_rest'

    def setUp(self):
        super(TestCreateCall, self).setUp()
        self.reset_ari()
        self.reset_confd()

    def test_create_call_with_correct_values(self):
        user_uuid = 'user-uuid'
        self.set_confd_users(MockUser(id='user-id', uuid='user-uuid'))
        self.set_confd_lines(MockLine(id='line-id', name='line-name', protocol='sip'))
        self.set_confd_user_lines({'user-id': [MockUserLine('user-id', 'line-id')]})
        self.set_ari_originates(MockChannel(id='new-call-id'))

        result = self.originate(source=user_uuid,
                                priority='my-priority',
                                extension='my-extension',
                                context='my-context')

        assert_that(result, has_entry('call_id', 'new-call-id'))
        assert_that(self.ari_requests(), has_entry('requests', has_item(has_entries({
            'method': 'POST',
            'path': '/ari/channels',
        }))))

    def test_when_create_call_then_ari_arguments_are_correct(self):
        user_uuid = 'user-uuid'
        self.set_confd_users(MockUser(id='user-id', uuid='user-uuid'))
        self.set_confd_lines(MockLine(id='line-id', name='line-name', protocol='sip'))
        self.set_confd_user_lines({'user-id': [MockUserLine('user-id', 'line-id')]})
        self.set_ari_originates(MockChannel(id='new-call-id'))

        self.originate(source=user_uuid,
                       priority='my-priority',
                       extension='my-extension',
                       context='my-context',
                       variables={'MY_VARIABLE': 'my-value',
                                  'SECOND_VARIABLE': 'my-second-value'})

        assert_that(self.ari_requests(), has_entry('requests', has_item(has_entries({
            'method': 'POST',
            'path': '/ari/channels',
            'query': has_items(['priority', 'my-priority'],
                               ['extension', 'my-extension'],
                               ['context', 'my-context'],
                               ['endpoint', 'sip/line-name']),
            'json': has_entries({'variables': {'MY_VARIABLE': 'my-value',
                                               'SECOND_VARIABLE': 'my-second-value'}}),
        }))))

    def test_when_create_call_with_no_variables_then_ari_variables_are_empty(self):
        user_uuid = 'user-uuid'
        self.set_confd_users(MockUser(id='user-id', uuid='user-uuid'))
        self.set_confd_lines(MockLine(id='line-id', name='line-name', protocol='sip'))
        self.set_confd_user_lines({'user-id': [MockUserLine('user-id', 'line-id')]})
        self.set_ari_originates(MockChannel(id='new-call-id'))

        self.originate(source=user_uuid,
                       priority='my-priority',
                       extension='my-extension',
                       context='my-context')

        assert_that(self.ari_requests(), has_entry('requests', has_item(has_entries({
            'method': 'POST',
            'path': '/ari/channels',
            'json': has_entries({'variables': {}}),
        }))))

    def test_create_call_with_multiple_lines(self):
        user_uuid = 'user-uuid'
        self.set_confd_users(MockUser(id='user-id', uuid='user-uuid'))
        self.set_confd_lines(MockLine(id='line-id', name='line-name', protocol='sip'))
        self.set_confd_user_lines({'user-id': [MockUserLine('user-id', 'line-id2', main_line=False),
                                               MockUserLine('user-id', 'line-id', main_line=True)]})
        self.set_ari_originates(MockChannel(id='new-call-id'))

        result = self.originate(source=user_uuid,
                                priority='my-priority',
                                extension='my-extension',
                                context='my-context')

        assert_that(result, has_entry('call_id', 'new-call-id'))
        assert_that(self.ari_requests(), has_entry('requests', has_item(has_entries({
            'method': 'POST',
            'path': '/ari/channels',
        }))))

    def test_create_call_with_no_lines(self):
        user_uuid = 'user-uuid'
        self.set_confd_users(MockUser(id='user-id', uuid='user-uuid'))
        self.set_confd_user_lines({'user-id': []})

        result = self.post_call_result(source=user_uuid,
                                       priority='my-priority',
                                       extension='my-extension',
                                       context='my-context',
                                       token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(400))
        assert_that(result.json(), has_entry('message', contains_string('line')))

    def test_create_call_with_invalid_user(self):
        user_uuid = 'user-uuid-not-found'

        result = self.post_call_result(source=user_uuid,
                                       priority='my-priority',
                                       extension='my-extension',
                                       context='my-context', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(400))
        assert_that(result.json(), has_entry('message', contains_string('user')))

    def test_create_call_with_missing_source(self):
        body = {'destination': {'priority': '1',
                                'extension': 'myexten',
                                'context': 'mycontext'}}
        result = self.post_call_raw(body, token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(400))
        assert_that(result.json(), has_entry('message', contains_string('source')))


class TestNoConfd(IntegrationTest):

    asset = 'no_confd'

    def setUp(self):
        super(TestNoConfd, self).setUp()
        self.reset_ari()

    def test_given_some_calls_and_no_confd_when_list_calls_then_503(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))
        self.set_ari_channel_variable({'first-id': {'XIVO_USERID': 'user1-id'},
                                       'second-id': {'XIVO_USERID': 'user2-id'}})

        result = self.get_calls_result(token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(503))

    def test_given_some_calls_and_no_confd_when_get_call_then_503(self):
        self.set_ari_channels(MockChannel(id='first-id'),
                              MockChannel(id='second-id'))
        self.set_ari_channel_variable({'first-id': {'XIVO_USERID': 'user1-id'},
                                       'second-id': {'XIVO_USERID': 'user2-id'}})

        result = self.get_call_result('first-id', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(503))

    def test_given_no_confd_when_originate_then_503(self):
        result = self.post_call_result(source='user-uuid',
                                       priority=None,
                                       extension=None,
                                       context=None,
                                       token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(503))


class TestNoARI(IntegrationTest):

    asset = 'no_ari'

    def test_given_no_ari_when_ctid_ng_starts_then_ctid_ng_stops(self):
        def ctid_ng_is_stopped():
            status = self.service_status()
            return not status['State']['Running']

        until.true(ctid_ng_is_stopped, tries=10, message='xivo-ctid-ng did not stop while starting with no ARI')

        log = self.service_logs()
        assert_that(log, contains_string("ARI server unreachable... stopping"))


class TestFailingARI(IntegrationTest):

    asset = 'failing_ari'

    def setUp(self):
        super(TestFailingARI, self).setUp()
        self.reset_confd()

    def test_given_no_ari_when_list_calls_then_503(self):
        result = self.get_calls_result(token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(503))

    def test_given_no_ari_when_get_call_then_503(self):
        result = self.get_call_result('first-id', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(503))

    def test_given_no_ari_when_originate_then_503(self):
        self.set_confd_users(MockUser(id='user-id', uuid='user-uuid'))
        self.set_confd_lines(MockLine(id='line-id', name='line-name', protocol='sip'))
        self.set_confd_user_lines({'user-id': [MockUserLine('user-id', 'line-id')]})
        result = self.post_call_result(source='user-uuid',
                                       priority='priority',
                                       extension='extension',
                                       context='context',
                                       token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(503))

    def test_given_no_ari_when_delete_call_then_503(self):
        result = self.delete_call_result('call-id', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(503))


class TestConnectUser(IntegrationTest):

    asset = 'basic_rest'

    def setUp(self):
        super(TestConnectUser, self).setUp()
        self.reset_ari()
        self.reset_confd()

    def test_given_one_call_and_one_user_when_connect_user_then_the_two_are_talking(self):
        self.set_ari_channels(MockChannel(id='call-id'),
                              MockChannel(id='new-call-id', ))
        self.set_ari_channel_variable({'new-call-id': {'XIVO_USERID': 'user-id'}})
        self.set_confd_users(MockUser(id='user-id', uuid='user-uuid'))
        self.set_confd_lines(MockLine(id='line-id', name='line-name', protocol='sip'))
        self.set_confd_user_lines({'user-id': [MockUserLine('user-id', 'line-id')]})
        self.set_ari_originates(MockChannel(id='new-call-id'))

        new_call = self.connect_user('call-id', 'user-id')

        assert_that(new_call, has_entries({
            'call_id': 'new-call-id'
        }))
        assert_that(self.ari_requests(), has_entry('requests', has_items(has_entries({
            'method': 'POST',
            'path': '/ari/channels',
            'query': contains_inanyorder(['app', 'callcontrol'], ['endpoint', 'sip/line-name'], ['appArgs', 'dialed_from,call-id']),
        }))))

    def test_given_no_user_when_connect_user_then_400(self):
        self.set_ari_channels(MockChannel(id='call-id'))

        result = self.put_call_user_result('call-id', 'user-id', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(400))
        assert_that(result.json(), has_entry('message', contains_string('user')))

    def test_given_user_has_no_line_when_connect_user_then_400(self):
        self.set_ari_channels(MockChannel(id='call-id'))
        self.set_confd_users(MockUser(id='user-id', uuid='user-uuid'))

        result = self.put_call_user_result('call-id', 'user-id', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(400))
        assert_that(result.json(), has_entry('message', contains_string('user')))

    def test_given_no_call_when_connect_user_then_404(self):
        self.set_confd_users(MockUser(id='user-id', uuid='user-uuid'))
        self.set_confd_lines(MockLine(id='line-id', name='line-name', protocol='sip'))
        self.set_confd_user_lines({'user-id': [MockUserLine('user-id', 'line-id')]})

        result = self.put_call_user_result('call-id', 'user-id', token=VALID_TOKEN)

        assert_that(result.status_code, equal_to(404))
        assert_that(result.json(), has_entry('message', contains_string('call')))
