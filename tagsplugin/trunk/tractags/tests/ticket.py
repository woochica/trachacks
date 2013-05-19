# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012,2013 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.util.compat import sorted
from trac.perm import PermissionCache, PermissionError, PermissionSystem
from trac.resource import Resource, ResourceNotFound
from trac.test import EnvironmentStub, Mock
from trac.ticket.model import Ticket
from trac.util.text import to_unicode

from tractags.api import TagSystem
from tractags.db import TagSetup
from tractags.ticket import TicketTagProvider


class TicketTagProviderTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        self.db = self.env.get_db_cnx()
        setup = TagSetup(self.env)
        setup.upgrade_environment(self.db)

        self.provider = TicketTagProvider(self.env)
        self.realm = 'ticket'
        self.tag_sys = TagSystem(self.env)
        self.tags = ['tag1']

        cursor = self.db.cursor()
        # Populate table with initial test data, not synced with tickets yet.
        cursor.execute("""
            INSERT INTO tags
                   (tagspace, name, tag)
            VALUES ('ticket', '1', 'deleted')""")
        self.realm = 'ticket'
        self._create_ticket(self.tags)

        self.req = Mock()
        # Mock an anonymous request.
        self.req.perm = PermissionCache(self.env)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _create_ticket(self, tags):
        ticket = Ticket(self.env)
        ticket['keywords'] = u' '.join(sorted(map(to_unicode, tags)))
        ticket['summary'] = 'summary'
        ticket.insert()

    def _tags(self):
        tags = {}
        cursor = self.db.cursor()
        cursor.execute("SELECT name,tag FROM tags")
        for name, tag in cursor.fetchall():
            if name in tags:
                tags[name].add(tag)
            else:
                tags[name] = set([tag])
        return tags

    # Tests

    def test_get_tags(self):
        resource = Resource('ticket', 2)
        self.assertRaises(ResourceNotFound, self.provider.get_resource_tags,
                          self.req, resource)
        self._create_ticket(self.tags)
        self.assertEquals(
            [tag for tag in
             self.provider.get_resource_tags(self.req, resource)], self.tags)
        #ignore_closed_tickets

    def test_set_tags(self):
        resource = Resource('ticket', 1)
        self.tags = ['tag2']
        # Anonymous lacks required permissions.
        self.assertRaises(PermissionError, self.provider.set_resource_tags,
                          self.req, resource, self.tags)
        self.req.authname = 'user'
        self.req.perm = PermissionCache(self.env, username='user')
        # Shouldn't raise an error with appropriate permission.
        self.provider.set_resource_tags(self.req, resource, self.tags)
        self.assertEquals(self.tag_sys.get_all_tags(self.req, '').keys(),
                          self.tags)

    def test_remove_tags(self):
        resource = Resource('ticket', 1)
        # Anonymous lacks required permissions.
        self.assertRaises(PermissionError, self.provider.remove_resource_tags,
                          self.req, resource)
        self.req.authname = 'user'
        self.req.perm = PermissionCache(self.env, username='user')
        # Shouldn't raise an error with appropriate permission.
        self.provider.remove_resource_tags(self.req, resource, 'comment')
        tkt = Ticket(self.env, 1)
        self.assertEquals(tkt['keywords'], '')

    def test_describe_tagged_resource(self):
        resource = Resource('ticket', 1)
        self.assertEquals(
            self.provider.describe_tagged_resource(self.req, resource),
            'defect: summary')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TicketTagProviderTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
