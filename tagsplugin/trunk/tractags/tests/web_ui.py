# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
import shutil
import tempfile

from trac.test import EnvironmentStub, Mock
from trac.perm import PermissionSystem, PermissionCache, PermissionError
from trac.web.href import Href
from trac.web.session import DetachedSession

from tractags.api import TagSystem
from tractags.model import TagModelProvider
from tractags.web_ui import TagRequestHandler


class TagRequestHandlerTestCase(unittest.TestCase):
    
    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        TagModelProvider(self.env).environment_created()
        
        self.tag_s = TagSystem(self.env)
        self.tag_rh = TagRequestHandler(self.env)
        
        perm_system = PermissionSystem(self.env)
        self.anonymous = PermissionCache(self.env, 'anonymous')
        self.reader = PermissionCache(self.env, 'reader')
        perm_system.grant_permission('reader', 'TAGS_VIEW')
        self.writer = PermissionCache(self.env, 'writer')
        perm_system.grant_permission('writer', 'TAGS_MODIFY')
        self.admin = PermissionCache(self.env, 'admin')
        perm_system.grant_permission('admin', 'TAGS_ADMIN')
        
        self.href = Href('/trac')
        self.abs_href = Href('http://example.org/trac')
    
    def tearDown(self):
        shutil.rmtree(self.env.path)
    
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
                   chrome={},
                   session=DetachedSession(self.env, 'reader'),
                   locale='',
                   tz=''
                )
        template, data, content_type = self.tag_rh.process_request(req)
        self.assertEquals('tag_view.html', template)
        self.assertEquals(None, content_type)
        self.assertEquals(['mincount', 'tag_body', 'tag_query', 'tag_realms',
                           'title'], sorted(data.keys()))
    
    def test_get_main_page_no_permission(self):
        req = Mock(path_info='/tags',
                   authname='anonymous',
                   perm=self.anonymous
                )
        self.assertRaises(PermissionError, self.tag_rh.process_request, req)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TagRequestHandlerTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
