# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest

import xmlrpclib
import os
import time

from trac.util.compat import sorted

from tracrpc.tests import rpc_testenv, TracRpcTestCase
from tracrpc.util import StringIO

class RpcWikiTestCase(TracRpcTestCase):
    
    def setUp(self):
        TracRpcTestCase.setUp(self)
        self.anon = xmlrpclib.ServerProxy(rpc_testenv.url_anon)
        self.user = xmlrpclib.ServerProxy(rpc_testenv.url_user)
        self.admin = xmlrpclib.ServerProxy(rpc_testenv.url_admin)

    def tearDown(self):
        TracRpcTestCase.tearDown(self)

    def test_attachments(self):
        # Note: Quite similar to the tracrpc.tests.json.JsonTestCase.test_binary
        image_url = os.path.join(rpc_testenv.trac_src, 'trac',
                             'htdocs', 'feed.png')
        image_in = StringIO(open(image_url, 'r').read())
        # Create attachment
        self.admin.wiki.putAttachmentEx('TitleIndex', 'feed2.png', 'test image',
            xmlrpclib.Binary(image_in.getvalue()))
        self.assertEquals(image_in.getvalue(), self.admin.wiki.getAttachment(
                                                'TitleIndex/feed2.png').data)
        # Update attachment (adding new)
        self.admin.wiki.putAttachmentEx('TitleIndex', 'feed2.png', 'test image',
            xmlrpclib.Binary(image_in.getvalue()), False)
        self.assertEquals(image_in.getvalue(), self.admin.wiki.getAttachment(
                                                'TitleIndex/feed2.2.png').data)
        # List attachments
        self.assertEquals(['TitleIndex/feed2.2.png', 'TitleIndex/feed2.png'],
                        sorted(self.admin.wiki.listAttachments('TitleIndex')))
        # Delete both attachments
        self.admin.wiki.deleteAttachment('TitleIndex/feed2.png')
        self.admin.wiki.deleteAttachment('TitleIndex/feed2.2.png')
        # List attachments again
        self.assertEquals([], self.admin.wiki.listAttachments('TitleIndex'))

    def test_getRecentChanges(self):
        self.admin.wiki.putPage('WikiOne', 'content one', {})
        time.sleep(1)
        self.admin.wiki.putPage('WikiTwo', 'content two', {})
        attrs2 = self.admin.wiki.getPageInfo('WikiTwo')
        changes = self.admin.wiki.getRecentChanges(attrs2['lastModified'])
        self.assertEquals(1, len(changes))
        self.assertEquals('WikiTwo', changes[0]['name'])
        self.assertEquals('admin', changes[0]['author'])
        self.assertEquals(1, changes[0]['version'])
        self.admin.wiki.deletePage('WikiOne')
        self.admin.wiki.deletePage('WikiTwo')

def test_suite():
    return unittest.makeSuite(RpcWikiTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
