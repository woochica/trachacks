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

from trac import __version__ as trac_version
from trac.core import Component, implements
from trac.db import Table, Column, Index
from trac.db.api import DatabaseManager
from trac.test import EnvironmentStub

from announcer import db_default
from announcer.api import AnnouncementSystem, AnnouncementEvent
from announcer.api import IAnnouncementSubscriptionFilter
from announcer.api import SubscriptionResolver


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


class AnnouncementSystemSetupTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)
        self.db = self.env.get_db_cnx()
        self.an_sys = AnnouncementSystem(self.env)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _get_cursor_description(self, cursor):
        # Cursors don't look the same across Trac versions
        if trac_version < '0.12':
            return cursor.description
        else:
            return cursor.cursor.description

    def _schema_init(self, schema=None):
        # Current announcer schema is setup with enabled component anyway.
        #   Revert these changes for clean install testing.
        cursor = self.db.cursor()
        cursor.execute("DROP TABLE IF EXISTS subscriptions")
        cursor.execute("DROP TABLE IF EXISTS subscription")
        cursor.execute("DROP TABLE IF EXISTS subscription_attribute")
        cursor.execute("DELETE FROM system WHERE name='announcer_version'")

        if schema:
            connector = self.db_mgr._get_connector()[0]
            for table in schema:
                for stmt in connector.to_sql(table):
                    cursor.execute(stmt)

    def _verify_curr_schema(self):
        self.assertFalse(self.an_sys.environment_needs_upgrade(self.db))
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM subscription_attribute")
        columns = [col[0] for col in self._get_cursor_description(cursor)]
        self.assertTrue('name' not in columns)
        self.assertTrue('value' not in columns)
        self.assertEquals(
            ['id', 'sid', 'authenticated', 'class', 'realm', 'target'],
            columns
        )
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='announcer_version'
        """)
        version = int(cursor.fetchone()[0])
        self.assertEquals(db_default.schema_version, version)

    def _verify_version_unregistered(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='announcer_version'
        """)
        self.assertFalse(cursor.fetchone())

    # Tests

    def test_new_install(self):
        # Just do db table clean-up.
        self._schema_init()

        self.assertEquals(0, self.an_sys.get_schema_version(self.db))
        self.assertTrue(self.an_sys.environment_needs_upgrade(self.db))

        self.an_sys.upgrade_environment(self.db)
        self._verify_curr_schema()

    def test_upgrade_v1_to_current(self):
        # The initial db schema from r3015 - 10-Jan-2008 by Stephen Hansen.
        schema = [
            Table('subscriptions', key='id')[
                Column('id', auto_increment=True),
                Column('sid'),
                Column('enabled', type='int'),
                Column('managed', type='int'),
                Column('realm'),
                Column('category'),
                Column('rule'),
                Column('destination'),
                Column('format'),
                Index(['id']),
                Index(['realm', 'category', 'enabled']),
            ]
        ]
        self._schema_init(schema)

        # Populate tables with test data.
        cursor = self.db.cursor()
        cursor.executemany("""
            INSERT INTO session
                   (sid,authenticated,last_visit)
            VALUES (%s,%s,%s)
        """, (('somebody','0','0'), ('user','1','0')))
        cursor.executemany("""
            INSERT INTO session_attribute
                   (sid,authenticated,name,value)
            VALUES (%s,1,%s,%s)
        """, (('user','announcer_email_format_ticket','text/html'),
              ('user','announcer_specified_email','')))
        cursor.executemany("""
            INSERT INTO subscriptions
                   (sid,enabled,managed,
                    realm,category,rule,destination,format)
            VALUES (%s,%s,0,%s,%s,%s,%s,%s)
        """, (('somebody',1,'ticket','changed','1','1','email'),
              ('user',1,'ticket','attachment added','1','1','email')))

        self.assertEquals(1, self.an_sys.get_schema_version(self.db))
        target = 6
        db_default.schema_version = target
        self.assertTrue(self.an_sys.environment_needs_upgrade(self.db))

        self.an_sys.upgrade_environment(self.db)
        self._verify_curr_schema()

    def test_upgrade_to_schema_v2(self):
        # The initial db schema from r3015 - 10-Jan-2008 by Stephen Hansen.
        schema = [
            Table('subscriptions', key='id')[
                Column('id', auto_increment=True),
                Column('sid'),
                Column('enabled', type='int'),
                Column('managed', type='int'),
                Column('realm'),
                Column('category'),
                Column('rule'),
                Column('destination'),
                Column('format'),
                Index(['id']),
                Index(['realm', 'category', 'enabled']),
            ]
        ]
        self._schema_init(schema)

        # Populate tables with test data.
        cursor = self.db.cursor()
        cursor.executemany("""
            INSERT INTO session
                   (sid,authenticated,last_visit)
            VALUES (%s,%s,%s)
        """, (('somebody','0','0'), ('user','1','0')))
        cursor.executemany("""
            INSERT INTO session_attribute
                   (sid,authenticated,name,value)
            VALUES (%s,1,%s,%s)
        """, (('user','announcer_email_format_ticket','text/html'),
              ('user','announcer_specified_email','')))
        cursor.executemany("""
            INSERT INTO subscriptions
                   (sid,enabled,managed,
                    realm,category,rule,destination,format)
            VALUES (%s,%s,0,%s,%s,%s,%s,%s)
        """, (('somebody',1,'ticket','changed','1','1','email'),
              ('user',1,'ticket','attachment added','1','1','email')))

        self.assertEquals(1, self.an_sys.get_schema_version(self.db))
        target = 2
        db_default.schema_version = target
        self.assertTrue(self.an_sys.environment_needs_upgrade(self.db))

        # Change from r3047 - 13-Jan-2008 for announcer-0.2 by Stephen Hansen.
        # - 'subscriptions.destination', 'subscriptions.format'
        # + 'subscriptions.authenticated', 'subscriptions.transport'
        # 'subscriptions.managed' type='int' --> (default == char)
        self.an_sys.upgrade_environment(self.db)

        self.assertEquals(target, self.an_sys.get_schema_version(self.db))
        self._verify_version_unregistered()
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM subscriptions")
        columns = [col[0] for col in self._get_cursor_description(cursor)]
        self.assertEquals(['id', 'sid', 'authenticated', 'enabled', 'managed',
                           'realm', 'category', 'rule', 'transport'],
                          columns
        )

    def test_upgrade_to_schema_v3(self):
        # Schema from r3047 - 13-Jan-2008 for announcer-0.2 by Stephen Hansen.
        schema = [
            Table('subscriptions', key='id')[
                Column('id', auto_increment=True),
                Column('sid'),
                Column('authenticated', type='int'),
                Column('enabled', type='int'),
                Column('managed'),
                Column('realm'),
                Column('category'),
                Column('rule'),
                Column('transport'),
                Index(['id']),
                Index(['realm', 'category', 'enabled']),
            ]
        ]
        self._schema_init(schema)

        # Populate tables with test data.
        cursor = self.db.cursor()
        cursor.executemany("""
            INSERT INTO session_attribute
                   (sid,authenticated,name,value)
            VALUES (%s,1,%s,%s)
        """, (('user','announcer_email_format_ticket','text/html'),
              ('user','announcer_email_format_wiki','text/plain'),
              ('user','announcer_specified_email','')))
        cursor.executemany("""
            INSERT INTO subscriptions
                   (sid,authenticated,enabled,managed,
                    realm,category,rule,transport)
            VALUES (%s,%s,1,%s,%s,%s,%s,%s)
        """, (('user',1,'watcher','ticket','changed','1','email'),
              ('user',1,'watcher','wiki','*','WikiStart','email')))

        self.assertEquals(2, self.an_sys.get_schema_version(self.db))
        target = 3
        db_default.schema_version = target
        self.assertTrue(self.an_sys.environment_needs_upgrade(self.db))

        # From r9116 - 25-Sep-2010 for announcer-0.12.1 by Robert Corsaro.
        # + table 'subscription', 'subscription_attribute'
        self.an_sys.upgrade_environment(self.db)

        self.assertEquals(target, self.an_sys.get_schema_version(self.db))

    def test_upgrade_to_schema_v4(self):
        # Schema from r9116 - 25-Sep-2010 for announcer-0.12.1 by R. Corsaro.
        schema = [
            Table('subscriptions', key='id')[
                Column('id', auto_increment=True),
                Column('sid'),
                Column('authenticated', type='int'),
                Column('enabled', type='int'),
                Column('managed'),
                Column('realm'),
                Column('category'),
                Column('rule'),
                Column('transport'),
                Index(['id']),
                Index(['realm', 'category', 'enabled']),
            ],
            Table('subscription', key='id')[
                Column('id', auto_increment=True),
                Column('time', type='int64'),
                Column('changetime', type='int64'),
                Column('class'),
                Column('sid'),
                Column('authenticated', type='int'),
                Column('distributor'),
                Column('format'),
                Column('priority'),
                Column('adverb')
            ],
            Table('subscription_attribute', key='id')[
                Column('id', auto_increment=True),
                Column('sid'),
                Column('class'),
                Column('name'),
                Column('value')
            ]
        ]
        self._schema_init(schema)

        # Populate tables with test data.
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO subscription
                   (time,changetime,class,sid,authenticated,
                    distributor,format,priority,adverb)
            VALUES ('0','0','GeneralWikiSubscriber','user','1',
                    'email','text/plain','1','always')
        """)
        cursor.executemany("""
            INSERT INTO subscription_attribute
                   (sid,class,name,value)
            VALUES (%s,%s,%s,%s)
        """, (('somebody','GeneralWikiSubscriber','wiki', '*'),
              ('somebody','UserChangeSubscriber','wiki','created'),
              ('user','GeneralWikiSubscriber','wiki', 'TracWiki')))

        self.assertEquals(3, self.an_sys.get_schema_version(self.db))
        target = 4
        db_default.schema_version = target
        self.assertTrue(self.an_sys.environment_needs_upgrade(self.db))

        # From r9210 - 29-Sep-2010 for announcer-0.12.1 by Robert Corsaro.
        # - table 'subscriptions'
        # 'subscription.priority' type=(default == char) --> 'int'
        # 'subscription_attribute.name --> 'subscription_attribute.realm'
        # 'subscription_attribute.value --> 'subscription_attribute.target'
        self.an_sys.upgrade_environment(self.db)

        self.assertEquals(target, self.an_sys.get_schema_version(self.db))
        # Check type of priority value.
        cursor = self.db.cursor()
        cursor.execute("SELECT priority FROM subscription")
        for priority in cursor:
            # Shouldn't raise an TypeError with appropriate column type.
            result = priority[0] + 0

    def test_upgrade_to_schema_v5(self):
        # Schema from r9210 - 29-Sep-2010 for announcer-0.12.1 by R. Corsaro.
        schema = [
            Table('subscription', key='id')[
                Column('id', auto_increment=True),
                Column('time', type='int64'),
                Column('changetime', type='int64'),
                Column('class'),
                Column('sid'),
                Column('authenticated', type='int'),
                Column('distributor'),
                Column('format'),
                Column('priority', type='int'),
                Column('adverb')
            ],
            Table('subscription_attribute', key='id')[
                Column('id', auto_increment=True),
                Column('sid'),
                Column('class'),
                Column('realm'),
                Column('target')
            ]
        ]
        self._schema_init(schema)

        # Populate tables with test data.
        cursor = self.db.cursor()
        cursor.executemany("""
            INSERT INTO session
                   (sid,authenticated,last_visit)
            VALUES (%s,%s,%s)
        """, (('somebody','0','0'), ('user','1','0')))
        cursor.executemany("""
            INSERT INTO subscription_attribute
                   (sid,class,realm,target)
            VALUES (%s,%s,%s,%s)
        """, (('somebody','GeneralWikiSubscriber','wiki', '*'),
              ('somebody','UserChangeSubscriber','wiki','created'),
              ('user','GeneralWikiSubscriber','wiki', 'TracWiki')))

        self.assertEquals(4, self.an_sys.get_schema_version(self.db))
        target = 5
        db_default.schema_version = target
        self.assertTrue(self.an_sys.environment_needs_upgrade(self.db))

        # From r9235 - 01-Oct-2010 for announcer-0.12.1 by Robert Corsaro.
        # + 'subscription_attribute.authenticated'
        self.an_sys.upgrade_environment(self.db)

        self.assertEquals(target, self.an_sys.get_schema_version(self.db))
        self._verify_version_unregistered()
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM subscription_attribute")
        columns = [col[0] for col in self._get_cursor_description(cursor)]
        self.assertTrue('name' not in columns)
        self.assertTrue('value' not in columns)
        self.assertEquals(
            ['id', 'sid', 'authenticated', 'class', 'realm', 'target'],
            columns
        )
        # Check authenticated attribute for session IDs.
        subscriptions = [(row[1],(row[2])) for row in cursor]
        for sub in subscriptions:
            self.assertTrue((sub[0] == 'user' and sub[1] == 1) or sub[1] == 0)

    def test_upgrade_to_schema_v6(self):
        # Check data migration and registration of unversioned schema.

        # Table definitions are identical to current schema here, see
        # schema from r9235 - 01-Oct-2010 for announcer-0.12.1 by R. Corsaro.
        self._schema_init(db_default.schema)

        # Populate table with test data.
        cursor = self.db.cursor()
        if self.env.config.get('trac', 'database').startswith('sqlite'):
            # Add dataset with CURRENT_TIMESTAMP strings.
            cursor.execute("""
                INSERT INTO subscription
                       (time,changetime,
                        class,sid,authenticated,
                        distributor,format,priority,adverb)
                VALUES ('1970-01-01 00:00:00','2012-10-31 23:59:59',
                        'GeneralWikiSubscriber','user','1',
                        'email','text/plain','1','always')
            """)
        else:
            cursor.execute("""
                INSERT INTO subscription
                       (time,changetime,
                        class,sid,authenticated,
                        distributor,format,priority,adverb)
                VALUES ('0','1351724399',
                        'GeneralWikiSubscriber','user','1',
                        'email','text/plain','1','always')
            """)
        cursor.execute("""
            INSERT INTO subscription_attribute
                   (sid,authenticated,class,realm,target)
            VALUES ('user','1','GeneralWikiSubscriber','wiki', 'TracWiki')
        """)
        self.assertEquals(5, self.an_sys.get_schema_version(self.db))
        target = 6
        db_default.schema_version = target
        self.assertTrue(self.an_sys.environment_needs_upgrade(self.db))

        # Data migration and registration of unversioned schema.
        self.an_sys.upgrade_environment(self.db)

        self._verify_curr_schema()
        cursor.execute("SELECT time,changetime FROM subscription")
        for time in cursor:
            # Shouldn't raise an TypeError with proper int/long values.
            check = time[1] - time[0]


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


class AnnouncementSystemSendTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'announcer.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)
        self.db = self.env.get_db_cnx()
        self.an_sys = AnnouncementSystem(self.env)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Tests

    def test_filter_added(self):
        class DummySubscriptionFilter(Component):
            """Test implementation for checking the filter ExtensionPoint."""
            implements(IAnnouncementSubscriptionFilter)

            def filter_subscriptions(self, event, subscriptions):
                """Just a pass-through."""
                return subscriptions

        dummy = DummySubscriptionFilter(self.env)
        self.assertTrue(dummy in self.an_sys.subscription_filters)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AnnouncementEventTestCase, 'test'))
    suite.addTest(unittest.makeSuite(AnnouncementSystemSetupTestCase, 'test'))
    suite.addTest(unittest.makeSuite(AnnouncementSystemSendTestCase, 'test'))
    suite.addTest(unittest.makeSuite(SubscriptionResolverTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
