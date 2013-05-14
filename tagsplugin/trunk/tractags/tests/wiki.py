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

try:
    from babel import Locale
except ImportError:
    Locale = None

from datetime import datetime

from trac.db.api import DatabaseManager
from trac.mimeview import Context
from trac.perm import PermissionCache, PermissionError, PermissionSystem
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.util.datefmt import utc
from trac.web.href import Href
from trac.wiki.model import WikiPage

from tractags.api import TagSystem
from tractags.db import TagSetup
from tractags.tests import formatter
from tractags.wiki import WikiTagProvider


TEST_CASES = u"""
============================== tag: link resolver for single tag
tag:onetag
tag:2ndtag n' more
tag:a.really_&nbsp;\wild-thing!
# regression test for ticket `#9057`
tag:single'quote
------------------------------
<p>
<a href="/tags?q=onetag">tag:onetag</a>
<a href="/tags?q=2ndtag">tag:2ndtag</a> n' more
<a href="/tags?q=a.really_%26nbsp%3B%5Cwild-thing!">tag:a.really_&amp;nbsp;\\wild-thing!</a>
# regression test for ticket <tt>#9057</tt>
<a href="/tags?q=single\'quote">tag:single\'quote</a>
</p>
------------------------------
============================== tagged: alternative link markup
tagged:onetag
tagged:'onetag 2ndtag'
------------------------------
<p>
<a href="/tags?q=onetag">tagged:onetag</a>
<a href="/tags?q=onetag+2ndtag">tagged:\'onetag 2ndtag\'</a>
</p>
------------------------------
============================== query expression in tag: link resolver
tag:'onetag 2ndtag'
tag:"onetag 2ndtag"
tag:'"heavily quoted"'
------------------------------
<p>
<a href="/tags?q=onetag+2ndtag">tag:\'onetag 2ndtag\'</a>
<a href="/tags?q=onetag+2ndtag">tag:\"onetag 2ndtag\"</a>
<a href="/tags?q=heavily+quoted">tag:\'"heavily quoted"\'</a>
</p>
------------------------------
============================== tag cleanup and quoting in tag: link resolver
# Trailing non-letter character must be ignored.
tag:onetag,
tag:onetag.
tag:onetag;
tag:onetag:
tag:onetag!
tag:onetag?
# Multiple trailing non-letter characters should be removed too.
tag:onetag..
tag:onetag...
------------------------------
<p>
# Trailing non-letter character must be ignored.
<a href="/tags?q=onetag">tag:onetag</a>,
<a href="/tags?q=onetag">tag:onetag</a>.
<a href="/tags?q=onetag">tag:onetag</a>;
<a href="/tags?q=onetag">tag:onetag</a>:
<a href="/tags?q=onetag">tag:onetag</a>!
<a href="/tags?q=onetag">tag:onetag</a>?
# Multiple trailing non-letter characters should be removed too.
<a href="/tags?q=onetag">tag:onetag</a>..
<a href="/tags?q=onetag">tag:onetag</a>...
</p>
============================== tag: as bracketed TracWiki link
[tag:onetag]
[tag:onetag label]
[tagged:onetag multi-word tag: label]
------------------------------
<p>
<a href="/tags?q=onetag">onetag</a>
<a href="/tags?q=onetag">label</a>
<a href="/tags?q=onetag">multi-word tag: label</a>
</p>
------------------------------
"""


class WikiTagProviderTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        self.tag_s = TagSystem(self.env)
        self.tag_wp = WikiTagProvider(self.env)

        self.db = self.env.get_db_cnx()
        setup = TagSetup(self.env)
        # Current tractags schema is partially setup with enabled component.
        #   Revert these changes for getting a clean setup.
        self._revert_tractags_schema_init()
        setup.upgrade_environment(self.db)

        cursor = self.db.cursor()
        # Populate table with initial test data.
        cursor.execute("""
            INSERT INTO tags
                   (tagspace, name, tag)
            VALUES ('wiki', 'WikiStart', 'tag1')
        """)

        self.req = Mock()
        # Mock an anonymous request.
        self.req.perm = PermissionCache(self.env)
        self.realm = 'wiki'
        self.tags = ['tag1']

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

    def test_get_tags(self):
        resource = Resource('wiki', 'WikiStart')
        self.assertEquals([tag for tag in
                           self.tag_wp.get_resource_tags(self.req, resource)],
                          self.tags)

    def test_exclude_template_tags(self):
        cursor = self.db.cursor()
        # Populate table with more test data.
        cursor.execute("""
            INSERT INTO tags
                   (tagspace, name, tag)
            VALUES ('wiki', 'PageTemplates/Template', 'tag2')
        """)
        tags = ['tag1', 'tag2']
        # Previous workaround for regression in query parser still works,
        #   but the query without argument works again as well.
        self.assertEquals(self.tag_s.get_all_tags(self.req, '-invalid').keys(),
                          self.tags)
        self.assertEquals(self.tag_s.get_all_tags(self.req, '').keys(),
                          self.tags)
        self.env.config.set('tags', 'query_exclude_wiki_templates', False)
        self.assertEquals(self.tag_s.get_all_tags(self.req, '-invalid').keys(),
                          tags)
        self.assertEquals(self.tag_s.get_all_tags(self.req, '').keys(),
                          tags)

    def test_set_tags_no_perms(self):
        resource = Resource('wiki', 'TaggedPage')
        self.assertRaises(PermissionError, self.tag_wp.set_resource_tags,
                          self.req, resource, self.tags)

    def test_set_tags(self):
        resource = Resource('wiki', 'TaggedPage')
        self.req.perm = PermissionCache(self.env, username='user')
        # Shouldn't raise an error with appropriate permission.
        self.tag_wp.set_resource_tags(self.req, resource, self.tags)


def wiki_setup(tc):
    tc.env = EnvironmentStub(default_data=True,
                             enable=['trac.*', 'tractags.*'])
    tc.env.path = tempfile.mkdtemp()
    tc.db_mgr = DatabaseManager(tc.env)
    tc.db = tc.env.get_db_cnx()

    TagSetup(tc.env).upgrade_environment(tc.db)

    now = datetime.now(utc)
    wiki = WikiPage(tc.env)
    wiki.name = 'TestPage'
    wiki.text = '--'
    wiki.save('joe', 'TagsPluginTestPage', '::1', now)

    req = Mock(href=Href('/'), abs_href=Href('http://www.example.com/'),
               authname='anonymous', perm=MockPerm(), tz=utc, args={},
               locale=Locale.parse('en_US') if Locale else None)
    tc.env.href = req.href
    tc.env.abs_href = req.abs_href
    tc.context = Context.from_request(req)
    # Enable big diff output.
    tc.maxDiff = None


def wiki_teardown(tc):
    tc.env.reset_db()
    tc.db.close()
    # Really close db connections.
    tc.env.shutdown()
    shutil.rmtree(tc.env.path)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(formatter.suite(TEST_CASES, wiki_setup, __file__,
                                  wiki_teardown))
    suite.addTest(unittest.makeSuite(WikiTagProviderTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
