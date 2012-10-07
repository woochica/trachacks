# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.test import EnvironmentStub, Mock
from trac.perm import PermissionSystem, PermissionCache, PermissionError
from trac.web.href import Href
from trac.web.session import DetachedSession

from tractags.api import TagSystem
from tractags.db import TagSetup
from tractags.web_ui import TagRequestHandler


class TagRequestHandlerTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()

        self.tag_s = TagSystem(self.env)
        self.tag_rh = TagRequestHandler(self.env)

        self.db = self.env.get_db_cnx()
        setup = TagSetup(self.env)
        # Current tractags schema is setup with enabled component anyway.
        #   Revert these changes for getting a clean setup.
        self._revert_tractags_schema_init()
        setup.upgrade_environment(self.db)

        perms = PermissionSystem(self.env)
        # Revoke default permissions, because more diversity is required here.
        perms.revoke_permission('anonymous', 'TAGS_VIEW')
        perms.revoke_permission('authenticated', 'TAGS_MODIFY')
        perms.grant_permission('reader', 'TAGS_VIEW')
        perms.grant_permission('writer', 'TAGS_MODIFY')
        perms.grant_permission('admin', 'TAGS_ADMIN')
        self.anonymous = PermissionCache(self.env)
        self.reader = PermissionCache(self.env, 'reader')
        self.writer = PermissionCache(self.env, 'writer')
        self.admin = PermissionCache(self.env, 'admin')

        self.href = Href('/trac')
        self.abs_href = Href('http://example.org/trac')

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _revert_tractags_schema_init(self):
        cursor = self.db.cursor()
        cursor.execute("DROP TABLE IF EXISTS tags")
        cursor.execute("DELETE FROM system WHERE name='tags_version'")
        cursor.execute("DELETE FROM permission WHERE action %s"
                       % self.db.like(), ('TAGS_%',))

    # Tests

    def test_matches(self):
        req = Mock(path_info='/tags',
                   authname='reader',
                   perm=self.reader
                  )
        self.assertEquals(True, self.tag_rh.match_request(req))

    def test_matches_no_permission(self):
        req = Mock(path_info='/tags',
                   authname='anonymous',
                   perm=self.anonymous
                  )
        self.assertEquals(False, self.tag_rh.match_request(req))

    def test_get_main_page(self):
        req = Mock(path_info='/tags',
                   args={},
                   authname='reader',
                   perm=self.reader,
                   href=self.href,
                   method='GET',
                   chrome=dict(static_hash='hashme!'),
                   session=DetachedSession(self.env, 'reader'),
                   locale='',
                   tz=''
                )
        template, data, content_type = self.tag_rh.process_request(req)
        self.assertEquals('tag_view.html', template)
        self.assertEquals(None, content_type)
        self.assertEquals(['checked_realms', 'mincount', 'page_title',
                           'tag_body', 'tag_query', 'tag_realms'],
                           sorted(data.keys()))

    def test_get_main_page_no_permission(self):
        req = Mock(path_info='/tags',
                   args={},
                   authname='anonymous',
                   perm=self.anonymous,
                   href=self.href,
                   chrome=dict(static_hash='hashme!'),
                   locale='',
                   tz=''
                )
        self.assertRaises(PermissionError, self.tag_rh.process_request, req)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagRequestHandlerTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
