# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest
import os
import shutil
import urllib2

from tracrpc.json_rpc import json
from tracrpc.util import StringIO

from tracrpc.tests import rpc_testenv, TracRpcTestCase

class JsonModuleAvailabilityTestCase(TracRpcTestCase):

    def setUp(self):
        TracRpcTestCase.setUp(self)

    def tearDown(self):
        TracRpcTestCase.tearDown(self)

    def test_json_not_available(self):
        if not json:
            # No json, so just make sure the protocol isn't there
            import tracrpc.json_rpc
            self.failIf(hasattr(tracrpc.json_rpc, 'JsonRpcProtocol'),
                        "JsonRpcProtocol really available?")
            return
        # Module manipulation to simulate json libs not available
        import sys
        old_json = sys.modules.get('json', None)
        sys.modules['json'] = None
        old_simplejson = sys.modules.get('simplejson', None)
        sys.modules['simplejson'] = None
        if 'tracrpc.json_rpc' in sys.modules:
            del sys.modules['tracrpc.json_rpc']
        try:
            import tracrpc.json_rpc
            self.failIf(hasattr(tracrpc.json_rpc, 'JsonRpcProtocol'),
                    "JsonRpcProtocol really available?")
        finally:
            del sys.modules['json']
            del sys.modules['simplejson']
            if old_json:
                sys.modules['json'] = old_json
            if old_simplejson:
                sys.modules['simplejson'] = old_simplejson
            if 'tracrpc.json_rpc' in sys.modules:
                del sys.modules['tracrpc.json_rpc']
            import tracrpc.json_rpc
            self.failIf(not hasattr(tracrpc.json_rpc, 'JsonRpcProtocol'),
                    "What, no JsonRpcProtocol?")

if not json:
    print "SKIP: json not available. Cannot run JsonTestCase."
    class JsonTestCase(TracRpcTestCase):
        pass
else:
    class JsonTestCase(TracRpcTestCase):

        def _anon_req(self, data):
            req = urllib2.Request(rpc_testenv.url_anon,
                        headers={'Content-Type': 'application/json'})
            req.data = json.dumps(data)
            resp = urllib2.urlopen(req)
            return json.loads(resp.read())

        def _auth_req(self, data, user='user'):
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            password_mgr.add_password(realm=None,
                          uri=rpc_testenv.url_auth,
                          user=user,
                          passwd=user)
            req = urllib2.Request(rpc_testenv.url_auth,
                        headers={'Content-Type': 'application/json'})
            req.data = json.dumps(data)
            resp = urllib2.build_opener(handler).open(req)
            return json.loads(resp.read())

        def setUp(self):
            TracRpcTestCase.setUp(self)

        def tearDown(self):
            TracRpcTestCase.tearDown(self)

        def test_call(self):
            result = self._anon_req(
                    {'method': 'system.listMethods', 'params': [], 'id': 244})
            self.assertTrue('system.methodHelp' in result['result'])
            self.assertEquals(None, result['error'])
            self.assertEquals(244, result['id'])

        def test_multicall(self):
            data = {'method': 'system.multicall', 'params': [
                    {'method': 'wiki.getAllPages', 'params': [], 'id': 1},
                    {'method': 'wiki.getPage', 'params': ['WikiStart', 1], 'id': 2},
                    {'method': 'ticket.status.getAll', 'params': [], 'id': 3},
                    {'method': 'nonexisting', 'params': []}
                ], 'id': 233}
            result = self._anon_req(data)
            self.assertEquals(None, result['error'])
            self.assertEquals(4, len(result['result']))
            items = result['result']
            self.assertEquals(1, items[0]['id'])
            self.assertEquals(233, items[3]['id'])
            self.assertTrue('WikiStart' in items[0]['result'])
            self.assertEquals(None, items[0]['error'])
            self.assertTrue('Welcome' in items[1]['result'])
            self.assertEquals(['accepted', 'assigned', 'closed', 'new',
                                    'reopened'], items[2]['result'])
            self.assertEquals(None, items[3]['result'])
            self.assertEquals('JSONRPCError', items[3]['error']['name'])

        def test_datetime(self):
            # read and write datetime values
            from datetime import datetime
            from trac.util.datefmt import utc
            dt_str = "2009-06-19T16:46:00"
            dt_dt = datetime(2009, 06, 19, 16, 46, 00, tzinfo=utc)
            data = {'method': 'ticket.milestone.update',
                'params': ['milestone1', {'due': {'__jsonclass__':
                    ['datetime', dt_str]}}]}
            result = self._auth_req(data, user='admin')
            self.assertEquals(None, result['error'])
            result = self._auth_req({'method': 'ticket.milestone.get',
                'params': ['milestone1']}, user='admin')
            self.assertTrue(result['result'])
            self.assertEquals(dt_str,
                        result['result']['due']['__jsonclass__'][1])

        def test_binary(self):
            # read and write binaries values
            image_url = os.path.join(rpc_testenv.trac_src, 'trac',
                                 'htdocs', 'feed.png')
            image_in = StringIO(open(image_url, 'r').read())
            data = {'method': 'wiki.putAttachmentEx',
                'params': ['TitleIndex', "feed2.png", "test image",
                {'__jsonclass__': ['binary', 
                            image_in.getvalue().encode("base64")]}]}
            result = self._auth_req(data, user='admin')
            self.assertEquals('feed2.png', result['result'])
            # Now try to get the attachment, and verify it is identical
            result = self._auth_req({'method': 'wiki.getAttachment',
                            'params': ['TitleIndex/feed2.png']}, user='admin')
            self.assertTrue(result['result'])
            image_out = StringIO(
                    result['result']['__jsonclass__'][1].decode("base64"))
            self.assertEquals(image_in.getvalue(), image_out.getvalue())

        def test_xmlrpc_permission(self):
            # Test returned response if not XML_RPC permission
            rpc_testenv._tracadmin('permission', 'remove', 'anonymous',
                                    'XML_RPC', wait=True)
            try:
                result = self._anon_req({'method': 'system.listMethods',
                                         'id': 'no-perm'})
                self.assertEquals(None, result['result'])
                self.assertEquals('no-perm', result['id'])
                self.assertEquals(403, result['error']['code'])
                self.assertTrue('XML_RPC' in result['error']['message'])
            finally:
                # Add back the default permission for further tests
                rpc_testenv._tracadmin('permission', 'add', 'anonymous',
                                            'XML_RPC', wait=True)

        def test_method_not_found(self):
            result = self._anon_req({'method': 'system.doesNotExist',
                                     'id': 'no-method'})
            self.assertTrue(result['error'])
            self.assertEquals(result['id'], 'no-method')
            self.assertEquals(None, result['result'])
            self.assertEquals(-32601, result['error']['code'])
            self.assertTrue('not found' in result['error']['message'])

        def test_wrong_argspec(self):
            result = self._anon_req({'method': 'system.listMethods',
                            'params': ['hello'], 'id': 'wrong-args'})
            self.assertTrue(result['error'])
            self.assertEquals(result['id'], 'wrong-args')
            self.assertEquals(None, result['result'])
            self.assertEquals(-32603, result['error']['code'])
            self.assertTrue('listMethods() takes exactly 2 arguments' \
                                in result['error']['message'])

        def test_call_permission(self):
            # Test missing call-specific permission
            result = self._anon_req({'method': 'ticket.component.delete',
                    'params': ['component1'], 'id': 2332})
            self.assertEquals(None, result['result'])
            self.assertEquals(2332, result['id'])
            self.assertEquals(403, result['error']['code'])
            self.assertTrue('TICKET_ADMIN privileges are required to '
                'perform this operation' in result['error']['message'])

        def test_resource_not_found(self):
            # A Ticket resource
            result = self._anon_req({'method': 'ticket.get',
                    'params': [2147483647], 'id': 3443})
            self.assertEquals(result['id'], 3443)
            self.assertEquals(result['error']['code'], 404)
            self.assertEquals(result['error']['message'],
                     'Ticket 2147483647 does not exist.')
            # A Wiki resource
            result = self._anon_req({'method': 'wiki.getPage',
                    'params': ["Test", 10], 'id': 3443})
            self.assertEquals(result['error']['code'], 404)
            self.assertEquals(result['error']['message'],
                     'Wiki page "Test" does not exist at version 10')

def test_suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(JsonModuleAvailabilityTestCase))
    test_suite.addTest(unittest.makeSuite(JsonTestCase))
    return test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
