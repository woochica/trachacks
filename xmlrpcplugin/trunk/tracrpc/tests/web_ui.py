# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest
import urllib2

from tracrpc.tests import rpc_testenv, TracRpcTestCase

class DocumentationTestCase(TracRpcTestCase):

    def setUp(self):
        TracRpcTestCase.setUp(self)
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        password_mgr.add_password(realm=None,
                      uri=rpc_testenv.url_auth,
                      user='user', passwd='user')
        self.opener_user = urllib2.build_opener(handler)

    def tearDown(self):
        TracRpcTestCase.tearDown(self)

    def test_get_with_content_type(self):
        req = urllib2.Request(rpc_testenv.url_auth,
                    headers={'Content-Type': 'text/html'})
        self.assert_rpcdocs_ok(self.opener_user, req)

    def test_get_no_content_type(self):
        req = urllib2.Request(rpc_testenv.url_auth)
        self.assert_rpcdocs_ok(self.opener_user, req)

    def test_post_accept(self):
        req = urllib2.Request(rpc_testenv.url_auth, 
                    headers={'Content-Type' : 'text/plain',
                              'Accept': 'application/x-trac-test,text/html'},
                    data='Pass since client accepts HTML')
        self.assert_rpcdocs_ok(self.opener_user, req)

        req = urllib2.Request(rpc_testenv.url_auth, 
                    headers={'Content-Type' : 'text/plain'},
                    data='Fail! No content type expected')
        self.assert_unsupported_media_type(self.opener_user, req)

    def test_form_submit(self):
        from urllib import urlencode
        # Explicit content type
        form_vars = {'result' : 'Fail! __FORM_TOKEN protection activated'}
        req = urllib2.Request(rpc_testenv.url_auth, 
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    data=urlencode(form_vars))
        self.assert_form_protect(self.opener_user, req)

        # Implicit content type
        req = urllib2.Request(rpc_testenv.url_auth, 
                    headers={'Accept': 'application/x-trac-test,text/html'},
                    data='Pass since client accepts HTML')
        self.assert_form_protect(self.opener_user, req)

    def test_get_dont_accept(self):
        req = urllib2.Request(rpc_testenv.url_auth, 
                    headers={'Accept': 'application/x-trac-test'})
        self.assert_unsupported_media_type(self.opener_user, req)

    def test_post_dont_accept(self):
        req = urllib2.Request(rpc_testenv.url_auth, 
                    headers={'Content-Type': 'text/plain',
                              'Accept': 'application/x-trac-test'},
                    data='Fail! Client cannot process HTML')
        self.assert_unsupported_media_type(self.opener_user, req)

    # Custom assertions
    def assert_rpcdocs_ok(self, opener, req):
        """Determine if RPC docs are ok"""
        try :
            resp = opener.open(req)
        except urllib2.HTTPError, e :
            self.fail("Request to '%s' failed (%s) %s" % (e.geturl(),
                                                          e.code,
                                                          e.fp.read()))
        else :
            self.assertEquals(200, resp.code)
            body = resp.read()
            self.assertTrue('<h3 id="XML-RPC">XML-RPC</h3>' in body)
            self.assertTrue('<h3 id="rpc.ticket.status">' in body)

    def assert_unsupported_media_type(self, opener, req):
        """Ensure HTTP 415 is returned back to the client"""
        try :
            opener.open(req)
        except urllib2.HTTPError, e:
            self.assertEquals(415, e.code)
            expected = "No protocol matching Content-Type '%s' at path '%s'." % \
                                (req.headers.get('Content-Type', 'text/plain'),
                                  '/login/rpc')
            got = e.fp.read()
            self.assertEquals(expected, got)
        except Exception, e:
            self.fail('Expected HTTP error but %s raised instead' % \
                                              (e.__class__.__name__,))
        else :
            self.fail('Expected HTTP error (415) but nothing raised')

    def assert_form_protect(self, opener, req):
        e = self.assertRaises(urllib2.HTTPError, opener.open, req)
        self.assertEquals(400, e.code)
        msg = e.fp.read()
        self.assertTrue("Missing or invalid form token. "
                                "Do you have cookies enabled?" in msg)

def test_suite():
    return unittest.makeSuite(DocumentationTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
