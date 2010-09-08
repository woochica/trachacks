# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
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
