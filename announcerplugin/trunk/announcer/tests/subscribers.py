# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.db.api import DatabaseManager
from trac.test import EnvironmentStub

from announcer.subscribers import CarbonCopySubscriber
from announcer.subscribers import TicketOwnerSubscriber
from announcer.subscribers import TicketReporterSubscriber
from announcer.subscribers import TicketUpdaterSubscriber


class SubscriberTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(
            enable=['trac.*', 'announcer.subscribers.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)
        self.db = self.env.get_db_cnx()

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)


class CarbonCopySubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that CarbonCopySubscriber initializes cleanly.
        CarbonCopySubscriber(self.env)
        pass


class TicketOwnerSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that TicketOwnerSubscriber initializes cleanly.
        TicketOwnerSubscriber(self.env)
        pass


class TicketReporterSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that TicketReporterSubscriber initializes
        #   cleanly.
        TicketReporterSubscriber(self.env)
        pass


class TicketUpdaterSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that TicketUpdaterSubscriber initializes
        #   cleanly.
        TicketUpdaterSubscriber(self.env)
        pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CarbonCopySubscriberTestCase, 'test'))
    suite.addTest(unittest.makeSuite(TicketOwnerSubscriberTestCase, 'test'))
    suite.addTest(unittest.makeSuite(TicketReporterSubscriberTestCase,
                                     'test'))
    suite.addTest(unittest.makeSuite(TicketUpdaterSubscriberTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
