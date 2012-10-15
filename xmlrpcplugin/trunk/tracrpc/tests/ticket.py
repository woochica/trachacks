# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009-2012 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest

import xmlrpclib
import os
import shutil
import datetime
import time

from tracrpc.tests import rpc_testenv, TracRpcTestCase

class RpcTicketTestCase(TracRpcTestCase):
    
    def setUp(self):
        TracRpcTestCase.setUp(self)
        self.anon = xmlrpclib.ServerProxy(rpc_testenv.url_anon)
        self.user = xmlrpclib.ServerProxy(rpc_testenv.url_user)
        self.admin = xmlrpclib.ServerProxy(rpc_testenv.url_admin)

    def tearDown(self):
        TracRpcTestCase.tearDown(self)

    def test_create_get_delete(self):
        tid = self.admin.ticket.create("create_get_delete", "fooy", {})
        tid, time_created, time_changed, attributes = self.admin.ticket.get(tid)
        self.assertEquals('fooy', attributes['description'])
        self.assertEquals('create_get_delete', attributes['summary'])
        self.assertEquals('new', attributes['status'])
        self.assertEquals('admin', attributes['reporter'])
        self.admin.ticket.delete(tid)

    def test_getActions(self):
        tid = self.admin.ticket.create("ticket_getActions", "kjsald", {})
        actions = self.admin.ticket.getActions(tid)
        default = [['leave', 'leave', '.', []], ['resolve', 'resolve',
                    "The resolution will be set. Next status will be 'closed'.",
                   [['action_resolve_resolve_resolution', 'fixed',
                  ['fixed', 'invalid', 'wontfix', 'duplicate', 'worksforme']]]],
                  ['reassign', 'reassign',
                  "The owner will change from (none). Next status will be 'assigned'.",
                  [['action_reassign_reassign_owner', 'admin', []]]],
                  ['accept', 'accept',
                  "The owner will change from (none) to admin. Next status will be 'accepted'.", []]]
        # Some action text was changed in trac:changeset:9041 - adjust default for test
        if 'will be changed' in actions[2][2]:
            default[2][2] = default[2][2].replace('will change', 'will be changed')
            default[3][2] = default[3][2].replace('will change', 'will be changed')
        self.assertEquals(actions, default)
        self.admin.ticket.delete(tid)

    def test_getAvailableActions_DeleteTicket(self):
        # http://trac-hacks.org/ticket/5387
        tid = self.admin.ticket.create('abc', 'def', {})
        self.assertEquals(False,
                'delete' in self.admin.ticket.getAvailableActions(tid))
        env = rpc_testenv.get_trac_environment()
        delete_plugin = os.path.join(rpc_testenv.tracdir,
                                    'plugins', 'DeleteTicket.py')
        shutil.copy(os.path.join(
            rpc_testenv.trac_src, 'sample-plugins', 'workflow', 'DeleteTicket.py'),
                    delete_plugin)
        env.config.set('ticket', 'workflow',
                'ConfigurableTicketWorkflow,DeleteTicketActionController')
        env.config.save()
        self.assertEquals(True,
                'delete' in self.admin.ticket.getAvailableActions(tid))
        self.assertEquals(False,
                'delete' in self.user.ticket.getAvailableActions(tid))
        env.config.set('ticket', 'workflow',
                'ConfigurableTicketWorkflow')
        env.config.save()
        rpc_testenv.restart()
        self.assertEquals(False,
                'delete' in self.admin.ticket.getAvailableActions(tid))
        # Clean up
        os.unlink(delete_plugin)
        rpc_testenv.restart()
        self.assertEquals(0, self.admin.ticket.delete(tid))

    def test_FineGrainedSecurity(self):
        self.assertEquals(1, self.admin.ticket.create('abc', '123', {}))
        self.assertEquals(2, self.admin.ticket.create('def', '456', {}))
        # First some non-restricted tests for comparison:
        self.assertRaises(xmlrpclib.Fault, self.anon.ticket.create, 'abc', 'def')
        self.assertEquals([1,2], self.user.ticket.query())
        self.assertTrue(self.user.ticket.get(2))
        self.assertTrue(self.user.ticket.update(1, "ok"))
        self.assertTrue(self.user.ticket.update(2, "ok"))
        # Enable security policy and test
        from trac.core import Component, implements
        from trac.perm import IPermissionPolicy
        policy = os.path.join(rpc_testenv.tracdir, 'plugins', 'TicketPolicy.py')
        open(policy, 'w').write(
        "from trac.core import *\n"
        "from trac.perm import IPermissionPolicy\n"
        "class TicketPolicy(Component):\n"
        "    implements(IPermissionPolicy)\n"
        "    def check_permission(self, action, username, resource, perm):\n"
        "        if username == 'user' and resource and resource.id == 2:\n"
        "            return False\n"
        "        if username == 'anonymous' and action == 'TICKET_CREATE':\n"
        "            return True\n")
        env = rpc_testenv.get_trac_environment()
        _old_conf = env.config.get('trac', 'permission_policies')
        env.config.set('trac', 'permission_policies', 'TicketPolicy,'+_old_conf)
        env.config.save()
        rpc_testenv.restart()
        self.assertEquals([1], self.user.ticket.query())
        self.assertTrue(self.user.ticket.get(1))
        self.assertRaises(xmlrpclib.Fault, self.user.ticket.get, 2)
        self.assertTrue(self.user.ticket.update(1, "ok"))
        self.assertRaises(xmlrpclib.Fault, self.user.ticket.update, 2, "not ok")
        self.assertEquals(3, self.anon.ticket.create('efg', '789', {}))
        # Clean, reset and simple verification
        env.config.set('trac', 'permission_policies', _old_conf)
        env.config.save()
        os.unlink(policy)
        rpc_testenv.restart()
        self.assertEquals([1,2,3], self.user.ticket.query())
        self.assertEquals(0, self.admin.ticket.delete(1))
        self.assertEquals(0, self.admin.ticket.delete(2))
        self.assertEquals(0, self.admin.ticket.delete(3))

    def test_getRecentChanges(self):
        tid1 = self.admin.ticket.create("ticket_getRecentChanges", "one", {})
        time.sleep(1)
        tid2 = self.admin.ticket.create("ticket_getRecentChanges", "two", {})
        _id, created, modified, attributes = self.admin.ticket.get(tid2)
        changes = self.admin.ticket.getRecentChanges(created)
        try:
            self.assertEquals(changes, [tid2])
        finally:
            self.admin.ticket.delete(tid1)
            self.admin.ticket.delete(tid2)

    def test_query_group_order_col(self):
        t1 = self.admin.ticket.create("1", "",
                        {'type': 'enhancement', 'owner': 'A'})
        t2 = self.admin.ticket.create("2", "", {'type': 'task', 'owner': 'B'})
        t3 = self.admin.ticket.create("3", "", {'type': 'defect', 'owner': 'A'})
        # order
        self.assertEquals([3,1,2], self.admin.ticket.query("order=type"))
        self.assertEquals([1,3,2], self.admin.ticket.query("order=owner"))
        self.assertEquals([2,1,3],
                        self.admin.ticket.query("order=owner&desc=1"))
        # group
        self.assertEquals([1,3,2], self.admin.ticket.query("group=owner"))
        self.assertEquals([2,1,3],
                        self.admin.ticket.query("group=owner&groupdesc=1"))
        # group + order
        self.assertEquals([2,3,1],
                self.admin.ticket.query("group=owner&groupdesc=1&order=type"))
        # col should just be ignored
        self.assertEquals([3,1,2],
                self.admin.ticket.query("order=type&col=status&col=reporter"))
        # clean
        self.assertEquals(0, self.admin.ticket.delete(t1))
        self.assertEquals(0, self.admin.ticket.delete(t2))
        self.assertEquals(0, self.admin.ticket.delete(t3))

    def test_query_special_character_escape(self):
        # Note: This test only passes when using Trac 0.12+
        # See http://trac-hacks.org/ticket/7737
        if __import__('trac').__version__ < '0.12':
            self.fail("Known issue: Trac 0.11 does not handle escaped input properly.")
        summary = ["here&now", "maybe|later", "back\slash"]
        search = ["here\&now", "maybe\|later", "back\\slash"]
        tids = []
        for s in summary:
            tids.append(self.admin.ticket.create(s,
                            "test_special_character_escape", {}))
        try:
            for i in range(0, 3):
                self.assertEquals([tids[i]],
                    self.admin.ticket.query("summary=%s" % search[i]))
            self.assertEquals(tids.sort(),
                    self.admin.ticket.query("summary=%s" % "|".join(search)).sort())
        finally:
            for tid in tids:
                self.admin.ticket.delete(tid)

    def test_update_author(self):
        tid = self.admin.ticket.create("ticket_update_author", "one", {})
        self.admin.ticket.update(tid, 'comment1', {})
        time.sleep(1)
        self.admin.ticket.update(tid, 'comment2', {}, False, 'foo')
        time.sleep(1)
        self.user.ticket.update(tid, 'comment3', {}, False, 'should_be_rejected')
        changes = self.admin.ticket.changeLog(tid)
        self.assertEquals(3, len(changes))
        for when, who, what, cnum, comment, _tid in changes:
            self.assertTrue(comment in ('comment1', 'comment2', 'comment3'))
            if comment == 'comment1':
                self.assertEquals('admin', who)
            if comment == 'comment2':
                self.assertEquals('foo', who)
            if comment == 'comment3':
                self.assertEquals('user', who)
        self.admin.ticket.delete(tid)

    def test_create_at_time(self):
        from trac.util.datefmt import to_datetime, utc
        now = to_datetime(None, utc)
        minus1 = now - datetime.timedelta(days=1)
        # create the tickets (user ticket will not be permitted to change time)
        one = self.admin.ticket.create("create_at_time1", "ok", {}, False,
                                        xmlrpclib.DateTime(minus1))
        two = self.user.ticket.create("create_at_time3", "ok", {}, False,
                                        xmlrpclib.DateTime(minus1))
        # get the tickets
        t1 = self.admin.ticket.get(one)
        t2 = self.admin.ticket.get(two)
        # check timestamps
        self.assertTrue(t1[1] < t2[1])
        self.admin.ticket.delete(one)
        self.admin.ticket.delete(two)

    def test_update_at_time(self):
        from trac.util.datefmt import to_datetime, utc
        now = to_datetime(None, utc)
        minus1 = now - datetime.timedelta(hours=1)
        minus2 = now - datetime.timedelta(hours=2)
        tid = self.admin.ticket.create("ticket_update_at_time", "ok", {})
        self.admin.ticket.update(tid, 'one', {}, False, '', xmlrpclib.DateTime(minus2))
        self.admin.ticket.update(tid, 'two', {}, False, '', xmlrpclib.DateTime(minus1))
        self.user.ticket.update(tid, 'three', {}, False, '', xmlrpclib.DateTime(minus1))
        time.sleep(1)
        self.user.ticket.update(tid, 'four', {})
        changes = self.admin.ticket.changeLog(tid)
        self.assertEquals(4, len(changes))
        # quick test to make sure each is older than previous
        self.assertTrue(changes[0][0] < changes[1][0] < changes[2][0])
        # margin of 2 seconds for tests
        justnow = xmlrpclib.DateTime(now - datetime.timedelta(seconds=1))
        self.assertTrue(justnow <= changes[2][0])
        self.assertTrue(justnow <= changes[3][0])
        self.admin.ticket.delete(tid)

    def test_update_non_existing(self):
        try:
            self.admin.ticket.update(3344, "a comment", {})
            self.fail("Allowed to update non-existing ticket???")
            self.admin.ticket.delete(3234)
        except Exception, e:
            self.assertTrue("Ticket 3344 does not exist." in str(e))

    def test_update_basic(self):
        import time
        # Basic update check, no 'action' or 'time_changed'
        tid = self.admin.ticket.create('test_update_basic1', 'ieidnsj', {
                        'owner': 'osimons'})
        # old-style (deprecated)
        self.admin.ticket.update(tid, "comment1", {'component': 'component2'})
        self.assertEquals(2, len(self.admin.ticket.changeLog(tid)))
        # new-style with 'action'
        time.sleep(1) # avoid "columns ticket, time, field are not unique"
        self.admin.ticket.update(tid, "comment2", {'component': 'component1',
                                                   'action': 'leave'})
        self.assertEquals(4, len(self.admin.ticket.changeLog(tid)))
        self.admin.ticket.delete(tid)

    def test_update_time_changed(self):
        # Update with collision check
        import datetime
        from tracrpc.util import to_utimestamp
        from tracrpc.xml_rpc import from_xmlrpc_datetime
        tid = self.admin.ticket.create('test_update_time_changed', '...', {})
        tid, created, modified, attrs = self.admin.ticket.get(tid)
        then = from_xmlrpc_datetime(modified) - datetime.timedelta(minutes=1)
        # Unrestricted old-style update (to be removed soon)
        try:
            self.admin.ticket.update(tid, "comment1",
                    {'_ts': str(to_utimestamp(then))})
        except Exception, e:
            self.assertTrue("Ticket has been updated since last get" in str(e))
        # Update with 'action' to test new-style update.
        try:
            self.admin.ticket.update(tid, "comment1",
                    {'_ts': str(to_utimestamp(then)),
                     'action': 'leave'})
        except Exception, e:
            self.assertTrue("modified by someone else" in str(e))
        self.admin.ticket.delete(tid)

    def test_update_time_same(self):
        # Unrestricted old-style update (to be removed soon)
        tid = self.admin.ticket.create('test_update_time_same', '...', {})
        tid, created, modified, attrs = self.admin.ticket.get(tid)
        ts = attrs['_ts']
        self.admin.ticket.update(tid, "comment1",
                    {'_ts': ts})
        self.admin.ticket.delete(tid)

        # Update with 'action' to test new-style update.
        tid = self.admin.ticket.create('test_update_time_same', '...', {})
        tid, created, modified, attrs = self.admin.ticket.get(tid)
        ts = attrs['_ts']
        self.admin.ticket.update(tid, "comment1",
                    {'_ts': ts, 'action': 'leave'})
        self.admin.ticket.delete(tid)

    def test_update_action(self):
        # Updating with 'action' in attributes
        tid = self.admin.ticket.create('test_update_action', 'ss')
        current = self.admin.ticket.get(tid)
        self.assertEqual('', current[3].get('owner', ''))
        updated = self.admin.ticket.update(tid, "comment1",
                {'action': 'reassign',
                 'action_reassign_reassign_owner': 'user'})
        self.assertEqual('user', updated[3].get('owner'))
        self.admin.ticket.delete(tid)

    def test_update_action_non_existing(self):
        # Updating with non-existing 'action' in attributes
        tid = self.admin.ticket.create('test_update_action_wrong', 'ss')
        try:
            self.admin.ticket.update(tid, "comment1",
                {'action': 'reassign',
                 'action_reassign_reassign_owner': 'user'})
        except Exception, e:
            self.assertTrue("invalid action" in str(e))
        self.admin.ticket.delete(tid)

    def test_update_field_non_existing(self):
        tid = self.admin.ticket.create('test_update_field_non_existing', 'yw3')
        try:
            self.admin.ticket.update(tid, "comment1",
                    {'does_not_exist': 'eiwrjoer'})
        except Exception, e:
            self.assertTrue("no such column" in str(e))
        self.admin.ticket.delete(tid)

    def test_create_ticket_9096(self):
        # See http://trac-hacks.org/ticket/9096
        import urllib2, base64
        body = """<?xml version="1.0"?>
                    <methodCall>
                        <methodName>ticket.create</methodName>
                        <params>
                            <param><string>test summary</string></param>
                            <param><string>test desc</string></param>
                        </params>
                    </methodCall>"""
        request = urllib2.Request(rpc_testenv.url + '/login/rpc', data=body)
        request.add_header('Content-Type', 'application/xml')
        request.add_header('Content-Length', str(len(body)))
        request.add_header('Authorization', 'Basic %s' \
                                 % base64.encodestring('admin:admin')[:-1])
        self.assertEquals('POST', request.get_method())
        response = urllib2.urlopen(request)
        self.assertEquals(200, response.code)
        self.assertEquals("<?xml version='1.0'?>\n"
                          "<methodResponse>\n"
                          "<params>\n"
                          "<param>\n"
                          "<value><int>1</int></value>\n"
                          "</param>\n"
                          "</params>\n"
                          "</methodResponse>\n", response.read())
        self.admin.ticket.delete(1)

class RpcTicketVersionTestCase(TracRpcTestCase):
    
    def setUp(self):
        TracRpcTestCase.setUp(self)
        self.anon = xmlrpclib.ServerProxy(rpc_testenv.url_anon)
        self.user = xmlrpclib.ServerProxy(rpc_testenv.url_user)
        self.admin = xmlrpclib.ServerProxy(rpc_testenv.url_admin)

    def tearDown(self):
        TracRpcTestCase.tearDown(self)

    def test_create(self):
        dt = xmlrpclib.DateTime(datetime.datetime.utcnow())
        desc = "test version"
        v = self.admin.ticket.version.create('9.99',
                            {'time': dt, 'description': desc})
        self.failUnless('9.99' in self.admin.ticket.version.getAll())
        self.assertEquals({'time': dt, 'description': desc, 'name': '9.99'},
                           self.admin.ticket.version.get('9.99'))

def test_suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(RpcTicketTestCase))
    test_suite.addTest(unittest.makeSuite(RpcTicketVersionTestCase))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
