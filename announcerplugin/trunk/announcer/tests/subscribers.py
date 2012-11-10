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

from announcer.subscribers import AllTicketSubscriber
from announcer.subscribers import CarbonCopySubscriber
from announcer.subscribers import GeneralWikiSubscriber
from announcer.subscribers import JoinableGroupSubscriber
from announcer.subscribers import TicketComponentOwnerSubscriber
from announcer.subscribers import TicketComponentSubscriber
from announcer.subscribers import TicketCustomFieldSubscriber
from announcer.subscribers import TicketOwnerSubscriber
from announcer.subscribers import TicketReporterSubscriber
from announcer.subscribers import TicketUpdaterSubscriber
from announcer.subscribers import UserChangeSubscriber
from announcer.subscribers import WatchSubscriber


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


class AllTicketSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        AllTicketSubscriber(self.env)
        pass


class CarbonCopySubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        CarbonCopySubscriber(self.env)
        pass


class GeneralWikiSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        GeneralWikiSubscriber(self.env)
        pass


class JoinableGroupSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        JoinableGroupSubscriber(self.env)
        pass


class TicketComponentOwnerSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        TicketComponentOwnerSubscriber(self.env)
        pass


class TicketComponentSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        TicketComponentSubscriber(self.env)
        pass


class TicketCustomFieldSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        TicketCustomFieldSubscriber(self.env)
        pass


class TicketOwnerSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        TicketOwnerSubscriber(self.env)
        pass


class TicketReporterSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        TicketReporterSubscriber(self.env)
        pass


class TicketUpdaterSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        TicketUpdaterSubscriber(self.env)
        pass


class UserChangeSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        UserChangeSubscriber(self.env)
        pass


class WatchSubscriberTestCase(SubscriberTestCase):

    def test_init(self):
        # Test just to confirm that AllTicketSubscriber initializes cleanly.
        WatchSubscriber(self.env)
        pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AllTicketSubscriberTestCase, 'test'))
    suite.addTest(unittest.makeSuite(CarbonCopySubscriberTestCase, 'test'))
    suite.addTest(unittest.makeSuite(GeneralWikiSubscriberTestCase, 'test'))
    suite.addTest(unittest.makeSuite(JoinableGroupSubscriberTestCase, 'test'))
    suite.addTest(unittest.makeSuite(TicketComponentOwnerSubscriberTestCase,
                                     'test'))
    suite.addTest(unittest.makeSuite(TicketComponentSubscriberTestCase,
                                     'test'))
    suite.addTest(unittest.makeSuite(TicketCustomFieldSubscriberTestCase,
                                     'test'))
    suite.addTest(unittest.makeSuite(TicketOwnerSubscriberTestCase, 'test'))
    suite.addTest(unittest.makeSuite(TicketReporterSubscriberTestCase,
                                     'test'))
    suite.addTest(unittest.makeSuite(TicketUpdaterSubscriberTestCase, 'test'))
    suite.addTest(unittest.makeSuite(UserChangeSubscriberTestCase, 'test'))
    suite.addTest(unittest.makeSuite(WatchSubscriberTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
