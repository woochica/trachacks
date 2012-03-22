# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import os
import unittest
import urllib2

from tracrpc.tests import rpc_testenv, TracRpcTestCase

from tracrpc.api import IRPCProtocol

from trac.core import *
from trac.test import Mock

class ProtocolProviderTestCase(TracRpcTestCase):

    def setUp(self):
        TracRpcTestCase.setUp(self)

    def tearDown(self):
        TracRpcTestCase.tearDown(self)

    def test_invalid_content_type(self):
        req = urllib2.Request(rpc_testenv.url_anon,
                    headers={'Content-Type': 'text/plain'},
                    data='Fail! No RPC for text/plain')
        try:
            resp = urllib2.urlopen(req)
            self.fail("Expected urllib2.HTTPError")
        except urllib2.HTTPError, e:
            self.assertEquals(e.code, 415)
            self.assertEquals(e.msg, "Unsupported Media Type")
            self.assertEquals(e.fp.read(),
                "No protocol matching Content-Type 'text/plain' at path '/rpc'.")

    def test_rpc_info(self):
        # Just try getting the docs for XML-RPC to test, it should always exist
        from tracrpc.xml_rpc import XmlRpcProtocol
        xmlrpc = XmlRpcProtocol(rpc_testenv.get_trac_environment())
        name, docs = xmlrpc.rpc_info()
        self.assertEquals(name, 'XML-RPC')
        self.assertTrue('Content-Type: application/xml' in docs)

    def test_valid_provider(self):
        # Confirm the request won't work before adding plugin
        req = urllib2.Request(rpc_testenv.url_anon,
                        headers={'Content-Type': 'application/x-tracrpc-test'},
                        data="Fail! No RPC for application/x-tracrpc-test")
        try:
            resp = urllib2.urlopen(req)
            self.fail("Expected urllib2.HTTPError")
        except urllib2.HTTPError, e:
            self.assertEquals(e.code, 415)
        # Make a new plugin 
        provider = os.path.join(rpc_testenv.tracdir, 'plugins', 'DummyProvider.py')
        open(provider, 'w').write(
            "from trac.core import *\n"
            "from tracrpc.api import *\n"
            "class DummyProvider(Component):\n"
            "    implements(IRPCProtocol)\n"
            "    def rpc_info(self):\n"
            "        return ('TEST-RPC', 'No Docs!')\n"
            "    def rpc_match(self):\n"
            "        yield ('rpc', 'application/x-tracrpc-test')\n"
            "    def parse_rpc_request(self, req, content_type):\n"
            "        return {'method' : 'system.getAPIVersion'}\n"
            "    def send_rpc_error(self, req, e):\n"
            "        rpcreq = req.rpc\n"
            "        req.send_error(None, template='', content_type=rpcreq['mimetype'],\n"
            "                       status=500, env=None, data='Test failure ')\n"
            "    def send_rpc_result(self, req, result):\n"
            "        rpcreq = req.rpc\n"
            "        # raise KeyError('Here')\n"
            "        response = 'Got a result!'\n"
            "        req.send(response, rpcreq['mimetype'], 200)\n")
        rpc_testenv.restart()
        try:
            req = urllib2.Request(rpc_testenv.url_anon,
                        headers={'Content-Type': 'application/x-tracrpc-test'})
            resp = urllib2.urlopen(req)
            self.assertEquals(200, resp.code)
            self.assertEquals("Got a result!", resp.read())
            self.assertEquals(resp.headers['Content-Type'],
                                  'application/x-tracrpc-test;charset=utf-8')
        finally:
            # Clean up so that provider don't affect further tests
            os.unlink(provider)
            rpc_testenv.restart()

    def test_general_provider_error(self):
        # Make a new plugin and restart server
        provider = os.path.join(rpc_testenv.tracdir, 'plugins', 'DummyProvider.py')
        open(provider, 'w').write(
            "from trac.core import *\n"
            "from tracrpc.api import *\n"
            "class DummyProvider(Component):\n"
            "    implements(IRPCProtocol)\n"
            "    def rpc_info(self):\n"
            "        return ('TEST-RPC', 'No Docs!')\n"
            "    def rpc_match(self):\n"
            "        yield ('rpc', 'application/x-tracrpc-test')\n"
            "    def parse_rpc_request(self, req, content_type):\n"
            "        return {'method' : 'system.getAPIVersion'}\n"
            "    def send_rpc_error(self, req, e):\n"
            "        if isinstance(e, RPCError) :\n"
            "            req.send_error(None, template='', \n"
            "                       content_type='text/plain',\n"
            "                       status=500, env=None, data=e.message)\n"
            "        else :\n"
            "            req.send_error(None, template='', \n"
            "                       content_type='text/plain',\n"
            "                       status=500, env=None, data='Test failure')\n"
            "    def send_rpc_result(self, req, result):\n"
            "        raise RPCError('No good.')")
        rpc_testenv.restart()
        # Make the request
        try:
            req = urllib2.Request(rpc_testenv.url_anon,
                        headers={'Content-Type': 'application/x-tracrpc-test'})
            resp = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            self.assertEquals(500, e.code)
            self.assertEquals("No good.", e.fp.read())
            self.assertTrue(e.hdrs['Content-Type'].startswith('text/plain'))
        finally:
            # Clean up so that provider don't affect further tests
            os.unlink(provider)
            rpc_testenv.restart()

def test_suite():
    return unittest.makeSuite(ProtocolProviderTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
