# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest

import xmlrpclib
import os
import shutil

from tracrpc.tests import rpc_testenv

class RpcTicketTestCase(unittest.TestCase):
    
    def setUp(self):
        self.anon = xmlrpclib.ServerProxy(rpc_testenv.url_anon)
        self.user = xmlrpclib.ServerProxy(rpc_testenv.url_user)
        self.admin = xmlrpclib.ServerProxy(rpc_testenv.url_admin)

    def test_getAvailableActions_DeleteTicket(self):
        # http://trac-hacks.org/ticket/5387
        tid = self.admin.ticket.create('abc', 'def', {})
        self.assertEquals(False,
                'delete' in self.admin.ticket.getAvailableActions(tid))
        env = rpc_testenv.get_trac_environment()
        shutil.copy(os.path.join(
            rpc_testenv.trac_src, 'sample-plugins', 'workflow', 'DeleteTicket.py'),
            os.path.join(rpc_testenv.tracdir, 'plugins'))
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
        
def suite():
    return unittest.makeSuite(RpcTicketTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
