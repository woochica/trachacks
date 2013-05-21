# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2013 ::: Jun Omae (jun66j5@gmail.com)
"""

import unittest

import xmlrpclib
import os
import shutil
import datetime
import time

from tracrpc.tests import rpc_testenv, TracRpcTestCase

class RpcSearchTestCase(TracRpcTestCase):

    def setUp(self):
        TracRpcTestCase.setUp(self)
        self.anon = xmlrpclib.ServerProxy(rpc_testenv.url_anon)
        self.user = xmlrpclib.ServerProxy(rpc_testenv.url_user)
        self.admin = xmlrpclib.ServerProxy(rpc_testenv.url_admin)

    def tearDown(self):
        TracRpcTestCase.tearDown(self)

    def test_fragment_in_search(self):
        t1 = self.admin.ticket.create("ticket10786", "",
                        {'type': 'enhancement', 'owner': 'A'})
        results = self.user.search.performSearch("ticket10786")
        self.assertEquals(1, len(results))
        self.assertEquals('<span class="new">#%d</span>: enhancement: '
                          'ticket10786 (new)' % t1,
                          results[0][1])
        self.assertEquals(0, self.admin.ticket.delete(t1))

def test_suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(RpcSearchTestCase))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
