# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.test import EnvironmentStub

from clients.client import ClientModule
from clients.model import Client


class ClientModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'clients.*'])
        self.cm = ClientModule(self.env)

    def tearDown(self):
        pass

    def test_implements_itemplateprovider(self):
        from trac.web.chrome import Chrome
        self.assertTrue(self.cm in Chrome(self.env).template_providers)

    def test_implements_iticketmanipulator(self):
        from trac.ticket.web_ui import TicketModule
        self.assertTrue(self.cm in TicketModule(self.env).ticket_manipulators)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ClientModuleTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

