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

from announcer.api import AnnouncementSystem
from announcer.model import Subscription, SubscriptionAttribute


class SubscriptionTestSetup(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)
        self.db = self.env.get_db_cnx()
        # Setup current announcer db schema tables.
        self.an_sys = AnnouncementSystem(self.env)
        self.an_sys.upgrade_environment(self.db)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)


class SubscriptionTestCase(SubscriptionTestSetup):
    def setUp(self):
        SubscriptionTestSetup.setUp(self)

        self.sub = Subscription(self.env)
        self.sub['sid'] = 'user'
        self.sub['authenticated'] = 1
        self.sub['distributor'] = 'email'
        self.sub['format'] = 'text/plain'
        self.sub['priority'] = 1
        self.sub['adverb'] = 'always'
        self.sub['class'] = 'GeneralWikiSubscriber'

    def test_init(self):
        # Examine properties of the initialized objekt.
        fields = ('id', 'sid', 'authenticated', 'distributor', 'format',
                  'priority', 'adverb', 'class')
        sub = Subscription(self.env)
        for field in fields:
            self.assertEqual(sub[field], None)
        # Check basic class method for subscription presentation too.
        sub = self.sub
        self.assertEqual(sub.subscription_tuple(),
                             (sub['class'], sub['distributor'], sub['sid'],
                              sub['authenticated'], None, sub['format'],
                              sub['priority'], sub['adverb']))

    def test_add_move_delete(self):
        sub = self.sub
        sub.add(self.env, sub)
        sql = """
            SELECT class,distributor,sid,authenticated,
                   NULL,format,priority,adverb
              FROM subscription
             WHERE priority=%s
        """
        cursor = self.db.cursor()
        cursor.execute(sql, (1,))
        for subscription in cursor.fetchall():
            self.assertEqual(subscription, sub.subscription_tuple())

        sub['class'] = 'UserChangeSubscriber'
        sub.add(self.env, sub)
        cursor.execute("SELECT COUNT(*) FROM subscription")
        count = cursor.fetchone()
        self.assertEqual(count[0], 2)

        sub.move(self.env, 1, 2)
        cursor.execute(sql, (1,))
        for subscription in cursor.fetchall():
            self.assertEqual(subscription[0], sub['class'])

        sub.delete(self.env, 1)
        cursor.execute("SELECT COUNT(*) FROM subscription")
        count = cursor.fetchone()
        self.assertEqual(count[0], 1)
        # Make sure, that we really deleted the 1st subscription.
        cursor.execute(sql, (1,))
        for subscription in cursor.fetchall():
            self.assertEqual(subscription[0], sub['class'])
        # Can't delete the same subscription twice.
        self.assertRaises(TypeError, sub.delete, self.env, 1)

    #def test_update_format_by_distributor_and_sid(self):

    #def test_find_by_sid_and_distributor(self):

    #def test_find_by_sids_and_class(self):

    #def test_find_by_class(self):


class SubscriptionAttributeTestCase(SubscriptionTestSetup):
    def test_init(self):
        # Examine properties of the initialized objekt.
        fields = ('id', 'sid', 'authenticated', 'class', 'realm', 'target')
        attr = SubscriptionAttribute(self.env)
        for field in fields:
            self.assertEqual(attr[field], None)

    def test_add_delete(self):
        attr = SubscriptionAttribute(self.env)
        attr.add(self.env, 'user', 1, 'GeneralWikiSubscriber','wiki',
                 ('TracWiki', 'TracWiki'))
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM subscription_attribute")
        count = cursor.fetchone()
        self.assertEqual(count[0], 2)

        attr.delete(self.env, 1)
        # Make sure, that we really deleted the 1st attribute.
        cursor.execute("SELECT target FROM subscription_attribute")
        for attribute in cursor.fetchone():
            self.assertEqual(attribute, 'TracWiki')
        cursor.execute("SELECT COUNT(*) FROM subscription_attribute")
        count = cursor.fetchone()
        self.assertEqual(count[0], 1)
        # Deleting non-existent subscriptions is handled gracefully.
        attr.delete(self.env, 1)

    #def test_delete_by_sid_and_class(self):

    #def test_delete_by_sid_class_and_target(self):

    #def test_delete_by_class_realm_and_target(self):

    #def test_find_by_sid_and_class(self):

    #def test_find_by_sid_class_and_target(self):

    #def test_find_by_sid_class_realm_and_target(self):

    #def test_find_by_class_realm_and_target(self):

    #def test_find_by_class_and_realm(self):


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SubscriptionTestCase, 'test'))
    suite.addTest(unittest.makeSuite(SubscriptionAttributeTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
