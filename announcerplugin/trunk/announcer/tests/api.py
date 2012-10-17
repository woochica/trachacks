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

from announcer.api import AnnouncementSystem, AnnouncementEvent, \
                          SubscriptionResolver


class AnnouncementEventTestCase(unittest.TestCase):
    def setUp(self):
        self.event = AnnouncementEvent('realm', 'category', 'target')

    # Tests

    def test_init(self):
        # Examine properties of the initialized objekt.
        event = self.event
        event_props = [event.realm, event.category, event.target, event.author]
        self.assertEquals(event_props, ['realm', 'category', 'target', ''])

    def test_get_basic_terms(self):
        # Method doesn't accept any argument.
        self.assertRaises(TypeError, self.event.get_basic_terms, None)
        self.assertEquals(self.event.get_basic_terms(), ('realm', 'category'))

    def test_get_session_terms(self):
        # While having mandatory argument, return value is a constant.
        self.assertRaises(TypeError, self.event.get_session_terms)
        self.assertEquals(self.event.get_session_terms(None), tuple())
        self.assertEquals(self.event.get_session_terms('anonymous'), tuple())


class AnnouncementSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)
        self.db = self.env.get_db_cnx()

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Tests

    def test_init(self):
        # Test just to confirm that AnnouncementSystem initializes cleanly
        #   and that setUp and tearDown both work.
        AnnouncementSystem(self.env)
        pass


class SubscriptionResolverTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)
        self.db = self.env.get_db_cnx()

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Tests

    def test_init(self):
        # Test just to confirm that SubscriptionResolver initializes cleanly
        #   and that setUp and tearDown both work.
        SubscriptionResolver(self.env)
        pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AnnouncementEventTestCase, 'test'))
    suite.addTest(unittest.makeSuite(AnnouncementSystemTestCase, 'test'))
    suite.addTest(unittest.makeSuite(SubscriptionResolverTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
